from __future__ import annotations
from typing import Dict, Any, Optional
import json
from pathlib import Path

from transformers import StoppingCriteria, StoppingCriteriaList


def _default_model_dir() -> Path:
    # model lives in: backend/src/llm/Phi-3.5-mini-instruct
    here = Path(__file__).resolve()
    src_dir = here.parents[2]  # .../backend/src
    return src_dir / "llm" / "Phi-3.5-mini-instruct"

def load_local_hf_pipeline(model_dir: Optional[str] = None):
    """
    Load a Transformers text-generation pipeline entirely from local files.
    Uses MPS on Apple Silicon when available. Fully offline.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    import torch
    import os
    from pathlib import Path

    def _default_model_dir() -> Path:
        # model lives in backend/src/llm/Qwen2.5-3B-Instruct
        here = Path(__file__).resolve()
        src_dir = here.parents[2]
        return src_dir / "llm" / "Qwen2.5-3B-Instruct"

    model_path = Path(model_dir) if model_dir else _default_model_dir()
    if not model_path.exists():
        raise FileNotFoundError(f"Local model path not found: {model_path}")

    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    # Device & dtype
    if torch.cuda.is_available():
        device_map = "auto"
        dtype = torch.float16
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device_map = {"": "mps"}          # change to "auto" if you want CPU offload
        dtype = torch.float16
    else:
        device_map = {"": "cpu"}
        dtype = torch.float32

    tok = AutoTokenizer.from_pretrained(
        str(model_path),
        trust_remote_code=True,
        local_files_only=True,
        use_fast=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        trust_remote_code=True,
        local_files_only=True,
        device_map=device_map,
        dtype=dtype,                    # <- use dtype (not torch_dtype)
        low_cpu_mem_usage=True,
        attn_implementation="eager",    # <- avoids flash-attn warning on Mac
        # caching_allocator_warmup=False,  # <- REMOVE this; Phi-3 doesn't support it
    ).eval()

    model.generation_config.use_cache = True

    # ensure a pad token to avoid warnings in greedy mode
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    return pipeline("text-generation", model=model, tokenizer=tok)


class StopOnSubstring(StoppingCriteria):
    """Stops generation once a given substring appears in the *generated* text."""
    def __init__(self, tokenizer, substring: str, prompt_tokens: int):
        self.tok = tokenizer
        self.substring = substring
        self.prompt_tokens = prompt_tokens

    def __call__(self, input_ids, scores, **kwargs):
        gen_ids = input_ids[0][self.prompt_tokens:]
        if len(gen_ids) == 0:
            return False
        text = self.tok.decode(gen_ids, skip_special_tokens=True)
        return self.substring in text


class HFJsonAdapter:
    """
    Wraps a local Hugging Face Transformers text-generation pipeline.
    No network requests; expects valid JSON from the model.
    """
    def __init__(self, text_generation_pipeline):
        self.pipe = text_generation_pipeline

    def classify(self, prompt: str, max_new_tokens: int = 256) -> Dict[str, Any]:
        tok = self.pipe.tokenizer
        pad_id = getattr(tok, "pad_token_id", None) or tok.eos_token_id

        enc = tok(prompt, return_tensors="pt")
        prompt_len_ids = enc["input_ids"].shape[-1]
        stop = StoppingCriteriaList([StopOnSubstring(tok, "</json>", prompt_len_ids)])

        out = self.pipe(
            prompt,
            max_new_tokens=max_new_tokens,     # give enough room to finish JSON
            do_sample=False,                   # greedy
            num_beams=1,
            use_cache=True,                    # cache back on for Qwen-3B
            pad_token_id=pad_id,
            return_full_text=False,
            stopping_criteria=stop,            # <- stop on </json>
        )
        if not out or "generated_text" not in out[0]:
            raise RuntimeError("HF pipeline returned no generated_text.")
        gen = out[0]["generated_text"]
        return self._extract_json(gen)


    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        s = text.strip()

        # Prefer tagged block
        start_tag = "<json>"
        end_tag = "</json>"
        if start_tag in s and end_tag in s:
            chunk = s.split(start_tag, 1)[1].split(end_tag, 1)[0].strip()
            return json.loads(chunk)

        # Fallback: first balanced {...}
        start = s.find("{")
        if start == -1:
            raise ValueError(f"No JSON object found.\n--- RAW ---\n{s[:2000]}")
        depth, end = 0, -1
        for i, ch in enumerate(s[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end == -1:
            raise ValueError(f"Incomplete JSON object.\n--- RAW ---\n{s[:2000]}")
        return json.loads(s[start:end])