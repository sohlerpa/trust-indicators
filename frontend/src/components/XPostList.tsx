import {XEmbed} from "react-social-media-embed";
import type {XPost} from "../api/types";
import FactCheckCard from "./FactCheckCard";

export default function XPostList({ posts }: { posts: XPost[] }) {
    console.log("x posts", posts)
    return (
        <div className="card">
            <h3>X</h3>

            <div className="list">
                {posts.map((p) => (
                    <div key={p.id} className="post">

                        {/* HEADER */}
                        <div className="postHeader">
                            <span
                                className={`badge ${p.indicators.badge}`}
                                title={p.indicators.badge}
                            />

                            <div className="factCheckWrapper">
                                <span className="factBadge">✓</span>

                                <div className="factPopover">
                                    <FactCheckCard id={p.id} type="x" />
                                </div>
                            </div>
                        </div>

                        {/* REAL X POST */}
                        <div style={{ margin: "8px 0 12px" }}>
                            <XEmbed url={p.url} />
                        </div>

                        {/* LOCAL METADATA */}
                        <div className="metaSmall">
                            {new Date(p.created_at).toLocaleString()}
                            URL {p.url}

                        </div>
                    </div>
                ))}

                {posts.length === 0 && (
                    <div className="hint">No posts match the current filters.</div>
                )}
            </div>
        </div>
    );
}