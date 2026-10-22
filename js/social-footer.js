/* Follow destinations supplied by the Ausmalwiese owner.
 * The Facebook share URL is accepted as one exact owner-provided exception.
 */
(() => {
  "use strict";

  const profiles = Object.freeze({
    instagram: "https://www.instagram.com/ausmalwiese/",
    facebook: "https://www.facebook.com/share/1F6tVwJ7QK/"
  });
  const platforms = [
    {
      key: "instagram",
      label: "Instagram",
      hosts: ["instagram.com", "www.instagram.com"],
      icon: '<rect x="2" y="2" width="20" height="20" rx="5"></rect><circle cx="12" cy="12" r="4"></circle><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"></circle>'
    },
    {
      key: "facebook",
      label: "Facebook",
      hosts: ["facebook.com", "www.facebook.com"],
      icon: '<path d="M15 21v-8h3l.5-4H15V7c0-1.1.4-2 2-2h2V1.5a21 21 0 0 0-2.8-.2C13 1.3 11 3.2 11 6.7V9H8v4h3v8"></path>'
    }
  ];

  function validatedProfileUrl(value, platform) {
    if (!value) return null;
    try {
      const url = new URL(value);
      if (url.protocol !== "https:" || url.username || url.password || url.port ||
          !platform.hosts.includes(url.hostname) || url.search || url.hash) return null;
      // The owner supplied this one Facebook share URL as the follow destination.
      // No other share URL is allowed by the ordinary profile-path rule below.
      if (platform.key === "facebook" &&
          url.href === "https://www.facebook.com/share/1F6tVwJ7QK/") return url.href;
      if (!/^\/[a-zA-Z0-9._-]+\/?$/.test(url.pathname)) return null;
      if (["explore", "reel", "reels", "p", "stories", "share", "sharer.php"].includes(url.pathname.split("/")[1])) return null;
      return url.href;
    } catch {
      return null;
    }
  }

  const links = platforms
    .map((platform) => ({ platform, url: validatedProfileUrl(profiles[platform.key], platform) }))
    .filter((entry) => entry.url);
  if (!links.length) return;

  const footer = document.createElement("footer");
  footer.className = "site-footer";
  const inner = document.createElement("div");
  inner.className = "container site-footer-inner";
  const heading = document.createElement("h2");
  heading.className = "site-footer-title";
  heading.textContent = "Folge uns";

  const nav = document.createElement("nav");
  nav.className = "site-footer-links";
  nav.setAttribute("aria-label", "Ausmalwiese in sozialen Netzwerken");
  for (const { platform, url } of links) {
    const link = document.createElement("a");
    link.className = "site-footer-link";
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", "Ausmalwiese auf " + platform.label + " öffnen (neuer Tab)");
    link.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
      platform.icon + '</svg><span>' + platform.label + '</span>';
    nav.append(link);
  }
  inner.append(heading, nav);
  footer.append(inner);
  document.body.append(footer);
})();
