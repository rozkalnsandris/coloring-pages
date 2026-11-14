/* #567: review-only Topic editorial and artwork manifest, not the runtime Topic registry. */
(() => {
  "use strict";
  const manifest = Object.freeze({
    schema: "rozkalns.ausmalwiese.topic-hero.v1",
    topics: Object.freeze({
      // Source-reviewed text and the exact owner-approved artwork; verified
      // Git blob 3b935fac2d9c817ff2d0fb8f004a539c8683bbf3 matches the prepared WebP.
      herbst: Object.freeze({
        intro: "Herbst-Ausmalbilder für Kinder: Entdecke Kürbisse, buntes Laub, Ernte-Motive, Laternen und weitere Ideen für gemütliche Herbsttage.",
        image: Object.freeze({
          src: "/assets/herbst-topic-hero.webp",
          width: 1755,
          height: 896,
          alt: "Ausmalwiese-Hund mit Kürbissen und buntem Herbstlaub",
          sha256: "d077de2efb5b291cf41140722958aa771fea6bd716da387a37458af700b0ad74",
          provenance: "ImageGen:dae01964-7ae9-4899-9663-9823c2602e24"
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