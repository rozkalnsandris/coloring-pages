(() => {
  "use strict";
  const BASE="/api/stats";
  const CAMPAIGN_IDS=new Set(["dortmund-01"]);
  const states=new Map();
  const INSTAGRAM_UTM_CAMPAIGNS = new Set(["profile", "story", "reel"]);

  // Tagged external arrivals are aggregate counts, not personal identities.
  function instagramLandingCampaign() {
    if (location.hostname !== "ausmalwiese.de" && location.hostname !== "www.ausmalwiese.de") return "";
    const params = new URLSearchParams(location.search);
    if (params.getAll("utm_source").length !== 1 || params.getAll("utm_medium").length !== 1
        || params.getAll("utm_campaign").length !== 1) return "";
    if (params.get("utm_source") !== "instagram" || params.get("utm_medium") !== "social") return "";
    const name = params.get("utm_campaign") || "";
    if (!INSTAGRAM_UTM_CAMPAIGNS.has(name)) return "";
    const navigation = performance.getEntriesByType?.("navigation")?.[0];
    if (navigation?.type === "reload") return "";
    if (document.referrer) {
      try {
        const from = new URL(document.referrer);
        if (from.hostname === "ausmalwiese.de" || from.hostname === "www.ausmalwiese.de") return "";
      } catch {
        // Suppressed/malformed external referrers do not prevent tagged landing.
      }
    }
    return "instagram-" + name;
  }

  const currentCampaign=()=>{
    const value=new URLSearchParams(location.search).get("campaign")||"";
    return CAMPAIGN_IDS.has(value)?value:"";
  };
  async function requestJson(path,options={}) {
    const response=await fetch(BASE+path,{
      cache:"no-store",credentials:"same-origin",...options,
      headers:{"Accept":"application/json",
        ...(options.body?{"Content-Type":"application/json"}:{}),
        ...(options.headers||{})}
    });
    if(!response.ok)throw new Error("stats request failed: "+response.status);
    return response.json();
  }
  const getRankings=(limit=6)=>requestJson("/rankings?limit="+Math.min(20,Math.max(1,Number(limit)||6)));
  const getOverview=()=>requestJson("/overview");
  const getTraffic=(days=7)=>requestJson("/traffic?days="+(Number(days)===30?30:7));
  const getCampaigns=(days=30)=>requestJson("/campaigns?days="+(Number(days)===7?7:30));

  async function getPage(pageId) {
    const data=await requestJson("/like/state?page_id="+encodeURIComponent(pageId));
    states.set(pageId,data);
    window.ColoringConsent?.syncFromServer?.(data.consented===true);
    return data;
  }
  async function toggleLike(pageId) {
    if(window.ColoringConsent?.allows?.("like")!==true)throw new Error("Like cookie consent required");
    const state=states.get(pageId);
    if(!state)throw new Error("Like state unavailable");
    const result=await requestJson("/like/choice",{
      method:"POST",body:JSON.stringify({page_id:pageId,liked:!state.liked})
    });
    states.set(pageId,result);
    return result;
  }
  async function enableLikeCookie() {
    const approved=await requestJson("/like/consent",{
      method:"POST",body:JSON.stringify({accept:true,version:1})
    });
    if(approved?.ok!==true)throw new Error("Like consent not confirmed");
    // HttpOnly cookies cannot be read by JS. Require server proof that the
    // browser actually returned it; otherwise never claim a saved Like.
    const session=await requestJson("/like/session");
    if(session?.consented!==true)throw new Error("Like cookie not available");
    return session;
  }
  async function disableLikeCookie() {
    const result=await requestJson("/like/forget",{
      method:"POST",body:JSON.stringify({confirm:true})
    });
    if(result?.revoked!==true)throw new Error("Like erasure not confirmed");
    states.clear();
    return result;
  }
  let oldEraseAttempted=false;
  async function eraseLegacyLikes() {
    if(oldEraseAttempted)throw new Error("Legacy erasure was already attempted");
    // Only explicit user-directed migration cleanup may read a legacy ID.
    let proof="";
    try { proof=localStorage.getItem("coloring-pages-visitor-v1")||""; }
    catch { throw new Error("Legacy proof inaccessible"); }
    const v2=/^v2-[0-9a-f]{64}$/.test(proof);
    const v3=/^v3-[0-9a-f]{64}$/.test(proof);
    if(!v2&&!v3)throw new Error("Legacy proof unavailable; use privacy contact");
    oldEraseAttempted=true; // never retry on ambiguous response
    const result=await requestJson(v3?"/erase-legacy-v3":"/erase-likes",{
      method:"POST",body:JSON.stringify({visitor_id:proof})
    });
    if(result?.ok!==true||result?.matched!==true)throw new Error("Legacy erasure not confirmed");
    try { if(localStorage.getItem("coloring-pages-visitor-v1")===proof)
      localStorage.removeItem("coloring-pages-visitor-v1"); } catch {}
    return result;
  }
  function trackVisit(stage="") {
    const campaign=currentCampaign();
    const instagram=campaign?"":instagramLandingCampaign();
    const body=campaign&&(stage==="landing"||stage==="catalog")
      ?{campaign,stage}:instagram?{campaign:instagram,stage:"landing"}:{};
    fetch(BASE+"/visit",{method:"POST",credentials:"same-origin",
      keepalive:true,headers:{"Content-Type":"application/json"},
      body:JSON.stringify(body)}).catch(()=>{});
  }
  function trackView(pageId) {
    const payload={page_id:pageId},campaign=currentCampaign();
    if(campaign)payload.campaign=campaign;
    const body=JSON.stringify(payload);
    if(navigator.sendBeacon) {
      try {if(navigator.sendBeacon(BASE+"/view",
        new Blob([body],{type:"application/json"})))return;}catch{}
    }
    fetch(BASE+"/view",{method:"POST",credentials:"same-origin",
      keepalive:true,headers:{"Content-Type":"application/json"},body}).catch(()=>{});
  }
  function trackPrint(pageId) {
    // Print counts are aggregate intent events: no visitor ID, browser storage
    // read, Like cookie inspection or separate consent gate.
    const payload={page_id:pageId},campaign=currentCampaign();
    if(campaign)payload.campaign=campaign;
    fetch(BASE+"/print-aggregate",{method:"POST",credentials:"same-origin",
      keepalive:true,headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)}).catch(()=>{});
  }
  window.ColoringStats={getRankings,getOverview,getTraffic,getCampaigns,
    getPage,toggleLike,trackVisit,trackView,trackPrint,
    enableLikeCookie,disableLikeCookie,eraseLegacyLikes};
  if(location.pathname==="/"||location.pathname==="/index.html")
    trackVisit(currentCampaign()?"catalog":"");
  if(location.pathname==="/detail.html")trackVisit();
})();