export async function onRequestGet(context) {
  const cf = context.request.cf || {};

  return new Response(
    JSON.stringify({
      ok: true,
      country: cf.country || "",
      city: cf.city || "",
      region: cf.region || "",
      continent: cf.continent || "",
      timezone: cf.timezone || "",
      latitude: cf.latitude || null,
      longitude: cf.longitude || null
    }),
    {
      headers: {
        "content-type": "application/json; charset=UTF-8",
        "cache-control": "no-store"
      }
    }
  );
}
