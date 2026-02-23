import {XEmbed} from "react-social-media-embed";
import type {XPost} from "../api/types";
import FactCheckCard from "./FactCheckCard";

export default function XPostList({ posts }: { posts: XPost[] }) {
    console.log("x posts", posts)
    return (
        <div className="card">
            <div className="list">
                {posts.map((p) => (
                    <div key={p.id} className="post">

                        {/* HEADER */}
                        <div className="postHeader itemTitle">

                            <div className="factCheckWrapper">
                                <button className="factButton">
                                    Fact check
                                </button>

                                <div className="factPopover">
                                    <FactCheckCard id={p.id} type="x" />
                                </div>
                            </div>
                        </div>

                        {/* REAL X POST */}
                        <div className="xEmbed">
                            <XEmbed url={p.url} />
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