import {XEmbed} from "react-social-media-embed";
import type {XPost} from "../api/types";
import FactCheckCard from "./FactCheckCard";

const BADGE_HINT: Record<string, string> = {
    grey: "There is not enough data about this post yet to compute the trust score. Wait until it is computed",
    green: "This post is likely to be trusted.",
        orange: "Handle this post with care.",
    red: "This post does not seem trustworthy.",
};

export default function XPostList({ posts }: { posts: XPost[] }) {
    console.log("x posts", posts)
    return (
        <div className="card">
            <div className="list">
                {posts.map((p) => (
                    <div key={p.id} className="post">

                        {/* HEADER */}
                        <div className="postHeader itemTitle">
                            <span className="badgeWrap">
                              <span className={`badge ${p.indicators.badge}`}/>
                              <span className="badgePopover">
                                <span className="badgeTooltip">
                                  {BADGE_HINT[p.indicators.badge]}
                                </span>
                              </span>
                            </span>

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