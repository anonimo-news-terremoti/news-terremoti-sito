import { initializeApp } from "https://www.gstatic.com/firebasejs/12.18.0/firebase-app.js";
import {
  getFirestore,
  collection,
  addDoc,
  query,
  orderBy,
  onSnapshot,
  serverTimestamp,
  limit,
  deleteDoc,
  doc
} from "https://www.gstatic.com/firebasejs/12.18.0/firebase-firestore.js";

import {
  getAuth,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/12.18.0/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyCrW23TMFTFRWWOdogA5bDhWBdbN5V4hyo",
  authDomain: "news-terremoti.firebaseapp.com",
  projectId: "news-terremoti",
  storageBucket: "news-terremoti.firebasestorage.app",
  messagingSenderId: "944750257608",
  appId: "1:944750257608:web:f0add770fcf35724810cfd",
  measurementId: "G-WC79E3M0FW"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

const ADMIN_UID = "V720CwqUJOh1DpHcoXq8bnhxo9k1";
const COMMENT_ADMIN_UID = "JCqSeAnDCjTlsSYVOx74zr8dwGH3";
let adminLogged = false;

const COMMENTS = collection(db, "guerra_comments");

const style = document.createElement("style");
style.textContent = `
.guerra-comments{
  margin-top:14px;
  padding-top:13px;
  border-top:1px solid rgba(102,190,230,.18);
}

.guerra-comments-head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  margin-bottom:10px;
  color:#9be8ff;
  font-size:13px;
  font-weight:900;
}

.guerra-comments-count{
  color:#79aec6;
  font-size:11px;
}

.guerra-comments-list{
  display:flex;
  flex-direction:column;
  gap:7px;
  margin-bottom:10px;
}

.guerra-comment{
  padding:9px 11px;
  border:1px solid rgba(93,198,241,.15);
  border-radius:10px;
  background:rgba(1,20,33,.65);
  color:#eaf8ff;
  font-size:13px;
  line-height:1.4;
}

.guerra-comment-name{
  display:block;
  margin-bottom:3px;
  color:#69d7ff;
  font-size:11px;
  font-weight:900;
}

.guerra-comment-date{
  display:block;
  margin-top:5px;
  color:#668fa4;
  font-size:9px;
}

.guerra-comment-form{
  display:grid;
  grid-template-columns:140px minmax(0,1fr) auto;
  gap:7px;
}

.guerra-comment-form input{
  min-width:0;
  padding:10px 11px;
  border:1px solid rgba(88,198,245,.25);
  border-radius:9px;
  outline:none;
  color:#fff;
  background:rgba(3,27,43,.9);
  font-size:13px;
}

.guerra-comment-form input:focus{
  border-color:#5acfff;
}

.guerra-comment-send{
  padding:10px 14px;
  border:1px solid rgba(71,205,255,.35);
  border-radius:9px;
  background:#075b83;
  color:#fff;
  font-weight:900;
  cursor:pointer;
}

.guerra-comment-send:hover{
  background:#0877a8;
}

.guerra-comment-status{
  margin-top:7px;
  min-height:14px;
  color:#7db3ca;
  font-size:10px;
}

.guerra-comment-delete{
  display:block;
  margin-top:8px;
  padding:6px 10px;
  border:1px solid rgba(255,80,80,.35);
  border-radius:7px;
  background:#8b1d28;
  color:#fff;
  font-size:11px;
  font-weight:800;
  cursor:pointer;
}

.guerra-comment-delete:hover{
  background:#b52735;
}

@media(max-width:650px){
  .guerra-comment-form{
    grid-template-columns:1fr;
  }

  .guerra-comment-send{
    width:100%;
  }
}
`;
document.head.appendChild(style);

const boxes = new Map();
let allComments = [];

function getPostId(card){
  const link = card.querySelector(".open")?.href || "";

  const match = link.match(/NEWSANONIMO\/(\d+)/i);
  if(match) return match[1];

  return encodeURIComponent(link || card.textContent.slice(0,80));
}

function formatDate(timestamp){
  try{
    if(timestamp?.toDate){
      return timestamp.toDate().toLocaleString("it-IT");
    }
  }catch(e){}

  return "adesso";
}

function renderBox(postId){
  const box = boxes.get(postId);
  if(!box) return;

  const list = box.querySelector(".guerra-comments-list");
  const count = box.querySelector(".guerra-comments-count");

  const comments = allComments
    .filter(c => String(c.postId) === String(postId))
    .slice(0,20);

  count.textContent =
    comments.length === 1
      ? "1 commento"
      : comments.length + " commenti";

  list.replaceChildren();

  comments.forEach(comment => {
    const row = document.createElement("div");
    row.className = "guerra-comment";

    const name = document.createElement("span");
    name.className = "guerra-comment-name";
    name.textContent = comment.name || "Anonimo";

    const text = document.createElement("div");
    text.textContent = comment.text || "";

    const date = document.createElement("span");
    date.className = "guerra-comment-date";
    date.textContent = formatDate(comment.createdAt);

    row.append(name,text,date);

    if(adminLogged){
      const del = document.createElement("button");
      del.className = "guerra-comment-delete";
      del.textContent = "🗑️ Elimina";

      del.addEventListener("click", async () => {
        if(!confirm("Eliminare definitivamente questo commento?")) return;

        del.disabled = true;
        del.textContent = "Eliminazione...";

        try{
          await deleteDoc(doc(db, "guerra_comments", comment.id));
        }catch(error){
          console.error("Errore eliminazione commento:", error);
          alert("❌ Impossibile eliminare il commento.");
          del.disabled = false;
          del.textContent = "🗑️ Elimina";
        }
      });

      row.append(del);
    }

    list.append(row);
  });
}

function renderAll(){
  boxes.forEach((_, postId) => renderBox(postId));
}

function addCommentsBox(card){
  if(card.dataset.commentsReady === "1") return;

  const body = card.querySelector(".card-body");
  if(!body) return;

  card.dataset.commentsReady = "1";

  const postId = getPostId(card);
  const postLink = card.querySelector(".open")?.href || "";

  const box = document.createElement("div");
  box.className = "guerra-comments";

  box.innerHTML = `
    <div class="guerra-comments-head">
      <span>💬 Commenti</span>
      <span class="guerra-comments-count">0 commenti</span>
    </div>

    <div class="guerra-comments-list"></div>

    <div class="guerra-comment-form">
      <input
        class="guerra-comment-name-input"
        type="text"
        maxlength="30"
        placeholder="Nome"
      >

      <input
        class="guerra-comment-text-input"
        type="text"
        maxlength="500"
        placeholder="Scrivi un commento..."
      >

      <button class="guerra-comment-send" type="button">
        Invia
      </button>
    </div>

    <div class="guerra-comment-status"></div>
  `;

  body.appendChild(box);
  boxes.set(postId, box);

  const nameInput = box.querySelector(".guerra-comment-name-input");
  const textInput = box.querySelector(".guerra-comment-text-input");
  const send = box.querySelector(".guerra-comment-send");
  const status = box.querySelector(".guerra-comment-status");

  try{
    nameInput.value = localStorage.getItem("guerra-comment-name") || "";
  }catch(e){}

  async function submit(){
    const name = nameInput.value.trim() || "Anonimo";
    const text = textInput.value.trim();

    if(!text){
      status.textContent = "Scrivi prima un commento.";
      return;
    }

    send.disabled = true;
    status.textContent = "Invio commento...";

    try{
      localStorage.setItem("guerra-comment-name", name);

      await addDoc(COMMENTS,{
        postId,
        postLink,
        name,
        text,
        createdAt: serverTimestamp()
      });

      textInput.value = "";
      status.textContent = "✅ Commento pubblicato";

      setTimeout(() => {
        status.textContent = "";
      },2500);

    }catch(error){
      console.error("Errore commento:",error);
      status.textContent =
        "❌ Impossibile pubblicare. Controllare Firestore.";
    }finally{
      send.disabled = false;
    }
  }

  send.addEventListener("click",submit);

  textInput.addEventListener("keydown",e => {
    if(e.key === "Enter"){
      submit();
    }
  });

  renderBox(postId);
}

function scanCards(){
  document.querySelectorAll("article.card").forEach(addCommentsBox);
}

scanCards();

const observer = new MutationObserver(() => {
  scanCards();
});

observer.observe(document.body,{
  childList:true,
  subtree:true
});

onAuthStateChanged(auth,user => {
  adminLogged = !!(
    user &&
    (
      user.uid === ADMIN_UID ||
      user.uid === COMMENT_ADMIN_UID
    )
  );
  renderAll();
});

const q = query(
  COMMENTS,
  orderBy("createdAt","desc"),
  limit(300)
);

onSnapshot(q,snapshot => {
  allComments = snapshot.docs.map(doc => ({
    id:doc.id,
    ...doc.data()
  }));

  renderAll();

},error => {
  console.error("Errore lettura commenti Firestore:",error);
});
