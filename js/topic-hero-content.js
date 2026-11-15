/* Generated from reviewed Hero metadata by render_landing_hero_topic_js.py.
   Do not edit this browser adapter directly. The managed Topic registry is /topics.json. */
(() => {
  "use strict";
  const manifest = Object.freeze({
    schema: "rozkalns.ausmalwiese.topic-hero.v1",
    topics: Object.freeze({
      "herbst": Object.freeze({
        intro: "Herbst-Ausmalbilder f\u00fcr Kinder: Entdecke K\u00fcrbisse, buntes Laub, Ernte-Motive, Laternen und weitere Ideen f\u00fcr gem\u00fctliche Herbsttage.",
        image: Object.freeze({
          src: "/assets/herbst-topic-hero.webp",
          width: 1755,
          height: 896,
          alt: "Ausmalwiese-Hund mit K\u00fcrbissen und buntem Herbstlaub",
          sha256: "d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74",
          provenance: "docs/TOPIC_HERO_ARTWORK_567.md",
          approval_ref: "coloring-pages#567"
        })
      })
    })
  });

  function get(topicId) {
    if (typeof topicId !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(topicId)) return null;
    const entry = Object.prototype.hasOwnProperty.call(manifest.topics, topicId)
      ? manifest.topics[topicId] : null;
    if (!entry) return null;
    const intro = typeof entry.intro === "string" && entry.intro.length <= 300
      ? entry.intro : "";
    const image = entry.image;
    const safeImage = image && image.src === "/assets/" + topicId + "-topic-hero.webp" &&
      Number.isInteger(image.width) && image.width > 0 &&
      Number.isInteger(image.height) && image.height > 0 &&
      typeof image.alt === "string" && image.alt.length > 0 && image.alt.length <= 180 &&
      /^[a-f0-9]{64}$/.test(image.sha256)
      ? image : null;
    return { intro, image: safeImage };
  }

  globalThis.AusmalTopicHero = Object.freeze({ schema: manifest.schema, get });
})();
