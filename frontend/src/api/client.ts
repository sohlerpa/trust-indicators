export async function apiGet<T>(path: string): Promise<T> {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
    return (await res.json()) as T;
}

export async function apiPost<T>(
    path: string,
    options: RequestInit
): Promise<T> {
    const res = await fetch(path, {
        headers: {
            "Content-Type": "application/json",
        },
        ...options,
    });

    if (!res.ok) {
        throw new Error(`API error ${res.status}: ${await res.text()}`);
    }

    return (await res.json()) as T;
}