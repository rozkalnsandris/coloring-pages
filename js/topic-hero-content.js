/* Generated from reviewed Hero metadata by render_landing_hero_topic_js.py.
   Do not edit this browser adapter directly. The managed Topic registry is /topics.json. */
(() => {
  "use strict";
  const manifest = Object.freeze({
    schema: "rozkalns.ausmalwiese.topic-hero.v1",
    topics: Object.freeze({
      "bauernhof": Object.freeze({
        intro: "Bauernhof-Ausmalbilder f\u00fcr Kinder: W\u00e4hle ein Motiv aus und drucke deine Malvorlage auf A4 aus.",
        image: Object.freeze({
          src: "/assets/bauernhof-topic-hero.webp",
          width: 1755,
          height: 896,
          alt: "Ausmalwiese-Hund neben einem gr\u00fcnen Traktor und einem gelben Bagger",
          sha256: "633c9565de757b6f0afaced8371ba5209fbb9dd3c41593441679450a98c51665",
          provenance: "docs/TOPIC_HERO_ARTWORK_594.md",
          approval_ref: "coloring-pages#594"
        })
      }),
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
      }),
      "weihnachten": Object.freeze({
        intro: "Weihnachten-Ausmalbilder f\u00fcr Kinder: W\u00e4hle eine Malvorlage aus und drucke sie kostenlos auf A4 aus.",
        image: Object.freeze({
          src: "/assets/weihnachten-topic-hero.webp",
          width: 1755,
          height: 896,
          alt: "Ausmalwiese-Hund neben einem geschm\u00fcckten Weihnachtsbaum und Geschenken im Schnee",
          sha256: "b5aaa55e6f9180a1dcd4bfceb03ba6285332390a0ad6c75bae819d8d6b34d1da",
          provenance: "docs/TOPIC_HERO_ARTWORK_596.md",
          approval_ref: "coloring-pages#596"
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
