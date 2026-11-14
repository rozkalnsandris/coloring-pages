/* #567: review-only Topic editorial and artwork manifest, not the runtime Topic registry. */
(() => {
  "use strict";
  const manifest = Object.freeze({
    schema: "rozkalns.ausmalwiese.topic-hero.v1",
    topics: Object.freeze({
      // The existing Herbst copy is already source-reviewed and published.
      // Approved artwork remains pending a verified binary GitHub handoff.
      herbst: Object.freeze({
        intro: "Herbst-Ausmalbilder für Kinder: Entdecke Kürbisse, buntes Laub, Ernte-Motive, Laternen und weitere Ideen für gemütliche Herbsttage."
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
    const safeImage = image && image.src === "/assets/topic-hero/" + topicId + ".webp" &&
      Number.isInteger(image.width) && image.width > 0 &&
      Number.isInteger(image.height) && image.height > 0 &&
      typeof image.alt === "string" && image.alt.length <= 180 &&
      /^[a-f0-9]{64}$/.test(image.sha256)
      ? image : null;
    return { intro, image: safeImage };
  }

  globalThis.AusmalTopicHero = Object.freeze({ schema: manifest.schema, get });
})();