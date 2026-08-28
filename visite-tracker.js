import { initializeApp, getApps } from
  "https://www.gstatic.com/firebasejs/12.18.0/firebase-app.js";

import {
  getFirestore,
  doc,
  setDoc,
  addDoc,
  collection
} from
  "https://www.gstatic.com/firebasejs/12.18.0/firebase-firestore.js";


const firebaseConfig = {
  apiKey: "AIzaSyCrW23TMFTFRWWOdogA5bDhWBdbN5V4hyo",
  authDomain: "news-terremoti.firebaseapp.com",
  projectId: "news-terremoti",
  storageBucket: "news-terremoti.firebasestorage.app",
  messagingSenderId: "944750257608",
  appId: "1:944750257608:web:f0add770fcf35724810cfd",
  measurementId: "G-WC79E3M0FW"
};


const app =
  getApps().length
    ? getApps()[0]
    : initializeApp(firebaseConfig);

const db = getFirestore(app);


function dispositivo() {
  const ua = navigator.userAgent || "";

  if (/ipad|tablet/i.test(ua))
    return "Tablet";

  if (/android|iphone|mobile/i.test(ua))
    return "Smartphone";

  return "Computer";
}


function browser() {
  const ua = navigator.userAgent || "";

  if (/edg/i.test(ua)) return "Edge";
  if (/firefox/i.test(ua)) return "Firefox";
  if (/chrome/i.test(ua)) return "Chrome";
  if (/safari/i.test(ua)) return "Safari";

  return "Altro";
}


function sistema() {
  const ua = navigator.userAgent || "";

  if (/android/i.test(ua)) return "Android";
  if (/iphone|ipad/i.test(ua)) return "iOS";
  if (/windows/i.test(ua)) return "Windows";
  if (/macintosh|mac os/i.test(ua)) return "macOS";
  if (/linux/i.test(ua)) return "Linux";

  return "Altro";
}


function provenienza() {
  try {
    if (!document.referrer)
      return "Diretto";

    const host =
      new URL(document.referrer).hostname
        .replace(/^www\./, "");

    if (host === location.hostname)
      return "Interno";

    return host;
  } catch {
    return "Diretto";
  }
}


function pagina() {
  if (document.title)
    return document.title.substring(0, 100);

  return location.pathname;
}


function sessione() {
  let id =
    sessionStorage.getItem(
      "anonimo_visit_session"
    );

  if (!id) {
    id =
      crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random()}`;

    sessionStorage.setItem(
      "anonimo_visit_session",
      id
    );
  }

  return id;
}


async function geo() {
  try {
    const r =
      await fetch(
        "https://anonimo-geo.twitchfratv1.workers.dev",
        { cache: "no-store" }
      );

    if (!r.ok)
      return {};

    return await r.json();

  } catch {
    return {};
  }
}


async function visitorInfo() {
  try {
    const r = await fetch(
      "https://anonimo-visitor-info.twitchfratv1.workers.dev",
      {
        cache: "no-store"
      }
    );

    if (!r.ok) {
      return {};
    }

    return await r.json();

  } catch {
    return {};
  }
}


async function avviaTracker() {

  try {

    const sid = sessione();

    const [g, visitor] =
      await Promise.all([
        geo(),
        visitorInfo()
      ]);

    const adesso = Date.now();

    const dati = {
      sessionId: sid,

      ip: visitor.ip || "",

      page: pagina(),
      path: location.pathname,

      referrer: provenienza(),

      device: dispositivo(),
      browser: browser(),
      os: sistema(),

      country: g.country || "",
      city: g.city || "",
      region: g.region || "",
      continent: g.continent || "",

      latitude:
        g.latitude
          ? Number(g.latitude)
          : null,

      longitude:
        g.longitude
          ? Number(g.longitude)
          : null,

      createdAtMs: adesso,
      lastSeenMs: adesso
    };


    // Registro una visita
    await addDoc(
      collection(db, "visite"),
      dati
    );


    // Registro presenza online
    const onlineRef =
      doc(
        db,
        "visitatori_online",
        sid
      );

    await setDoc(
      onlineRef,
      dati,
      { merge: true }
    );


    // Heartbeat ogni 30 secondi
    setInterval(
      async () => {
        try {
          await setDoc(
            onlineRef,
            {
              ...dati,
              page: pagina(),
              path: location.pathname,
              lastSeenMs: Date.now()
            },
            { merge: true }
          );
        } catch {}
      },
      30000
    );

  } catch (errore) {

    console.warn(
      "Tracker visite non disponibile:",
      errore
    );
  }
}


avviaTracker();
