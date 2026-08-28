export async function onRequestGet(context) {
  const request = context.request;
  const cf = request.cf || {};

  let ip =
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("X-Forwarded-For") ||
    "";

  if (ip.includes(",")) {
    ip = ip.split(",")[0].trim();
  }

  return new Response(
    JSON.stringify({
      ip: ip || "",
      city: cf.city || "",
      region: cf.region || "",
      country: cf.country || "",
      continent: cf.continent || "",
      timezone: cf.timezone || ""
    }),
    {
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*"
      }
    }
  );
}
