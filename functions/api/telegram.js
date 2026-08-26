const CHANNEL = "NEWSANONIMO";
const TELEGRAM_PUBLIC_URL = `https://t.me/s/${CHANNEL}`;

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=60, s-maxage=60",
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
      "access-control-allow-headers": "Content-Type",
    },
  });
}

function normalizeText(value) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function createCollector() {
  return {
    posts: [],
    current: null,
  };
}

export async function onRequest(context) {
  const request = context.request;

  if (request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, OPTIONS",
        "access-control-allow-headers": "Content-Type",
      },
    });
  }

  if (request.method !== "GET") {
    return json({ error: "Metodo non consentito" }, 405);
  }

  try {
    const upstream = await fetch(TELEGRAM_PUBLIC_URL, {
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; AnonimoNewsTerremoti/1.0)",
        "Accept": "text/html,application/xhtml+xml",
      },
      cf: {
        cacheTtl: 60,
        cacheEverything: true,
      },
    });

    if (!upstream.ok) {
      return json({ error: `Telegram HTTP ${upstream.status}` }, 502);
    }

    const collector = createCollector();

    const rewriter = new HTMLRewriter()
      .on(".tgme_widget_message", {
        element(element) {
          const dataPost = element.getAttribute("data-post") || "";
          const parts = dataPost.split("/");
          const id = Number(parts[1]) || 0;

          const post = {
            id,
            text: "",
            link: id ? `https://t.me/${CHANNEL}/${id}` : `https://t.me/${CHANNEL}`,
            pubDate: "",
          };

          collector.current = post;

          element.onEndTag(() => {
            post.text = normalizeText(post.text);
            if (!post.text) {
              post.text = "Nuovo aggiornamento pubblicato sul canale.";
            }
            collector.posts.push(post);
            if (collector.current === post) collector.current = null;
          });
        },
      })
      .on(".tgme_widget_message_text", {
        text(chunk) {
          if (collector.current) collector.current.text += chunk.text;
        },
      })
      .on(".tgme_widget_message_caption", {
        text(chunk) {
          if (collector.current) collector.current.text += " " + chunk.text;
        },
      })
      .on(".tgme_widget_message_date", {
        element(element) {
          if (!collector.current) return;
          const href = element.getAttribute("href");
          if (href) collector.current.link = href;
        },
      })
      .on(".tgme_widget_message_date time", {
        element(element) {
          if (!collector.current) return;
          const datetime = element.getAttribute("datetime");
          if (datetime) collector.current.pubDate = datetime;
        },
      });

    await rewriter.transform(upstream).text();

    const seen = new Set();
    const posts = collector.posts
      .filter((post) => {
        const key = post.id || post.link;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort((a, b) => b.id - a.id)
      .slice(0, 5)
      .map(({ id, text, link, pubDate }) => ({ id, text, link, pubDate }));

    if (!posts.length) {
      return json({ error: "Nessun post Telegram trovato" }, 502);
    }

    return json({
      ok: true,
      channel: CHANNEL,
      updatedAt: new Date().toISOString(),
      posts,
    });
  } catch (error) {
    return json(
      {
        error: "Errore durante il recupero dei post Telegram",
        detail: String(error?.message || error),
      },
      500,
    );
  }
}
