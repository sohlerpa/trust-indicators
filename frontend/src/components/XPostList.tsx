import type {XPost} from "../api/types";

export default function XPostList({posts}: { posts: XPost[] }) {
    return (
        <div className="card">
            <h3>X</h3>
            <div className="list">
                {posts.map((p) => (
                    <div key={p.id} className="post">
                        <div className="postHeader">
                            <div>
                                <strong>{p.display_name}</strong> <span className="metaSmall">{p.handle}</span>
                            </div>
                            <span className={`badge ${p.indicators.badge}`} title={p.indicators.badge}/>
                        </div>
                        <div>{p.text}</div>
                        <div className="metaSmall">{new Date(p.created_at).toLocaleString()}</div>
                    </div>
                ))}
                {posts.length === 0 && <div className="hint">No posts match the current filters.</div>}
            </div>
        </div>
    );
}
