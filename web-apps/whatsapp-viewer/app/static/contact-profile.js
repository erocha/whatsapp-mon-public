const profileEscape = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
const profileInitials = (name) => (name || "?").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();

async function profileApi(url) {
  const response = await fetch(url);
  if (response.status === 401) { location = "/login"; return null; }
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function profileMedia(item) {
  const mime = item.mime_type || "";
  const url = `/media/${item.message_id}`;
  if (mime.startsWith("image/")) return `<a href="${url}" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="${url}" alt="Mídia"></a>`;
  const icon = mime.startsWith("video/") ? "▶" : mime.startsWith("audio/") ? "♪" : "▤";
  return `<a class="profile-media-file" href="${url}" target="_blank" rel="noopener noreferrer"><b>${icon}</b><small>${profileEscape(item.media_name || mime || "Arquivo")}</small></a>`;
}

async function showContactProfile(url) {
  const body = document.querySelector("#detailsBody");
  document.querySelector("#app").classList.add("details-open");
  body.innerHTML = '<div class="profile-loading">Carregando contato…</div>';
  try {
    const profile = await profileApi(url);
    if (!profile) return;
    const phone = profile.phone ? `+${profile.phone}` : "Número não disponível no backup";
    const photoUrl = `/api/contact-photo?jid=${encodeURIComponent(profile.jid)}`;
    const media = profile.media.map(profileMedia).join("") || '<p class="muted">Nenhuma mídia disponível.</p>';
    const groups = profile.groups.map((group) => `<button class="common-group" data-chat-id="${group.chat_id}" data-jid="${profileEscape(group.jid)}" data-name="${profileEscape(group.subject || group.jid)}"><span class="avatar">${profileEscape(profileInitials(group.subject || group.jid))}</span><span><b>${profileEscape(group.subject || group.jid)}</b><small>${Number(group.group_member_count || 0).toLocaleString("pt-BR")} participantes</small></span></button>`).join("") || '<p class="muted">Nenhum grupo em comum encontrado no backup.</p>';
    body.innerHTML = `<section class="contact-profile"><div class="profile-hero"><div class="profile-photo"><span>${profileEscape(profileInitials(profile.name))}</span>${profile.has_photo ? `<img src="${photoUrl}" alt="Foto de ${profileEscape(profile.name)}" onerror="this.remove()">` : ""}</div><h2>${profileEscape(profile.name)}</h2><button class="profile-identity" type="button" title="Identificador no banco">${profileEscape(phone)}</button><small>${profileEscape(profile.jid)}</small><div class="profile-actions"><button type="button" class="profile-open-chat" ${profile.direct_chat_id ? "" : "disabled"}>▤<span>Conversar</span></button><button type="button" disabled>☎<span>Voz</span></button><button type="button" disabled>▣<span>Vídeo</span></button></div></div><section class="profile-section"><h3>Mídia, links e docs <span>${Number(profile.media_count).toLocaleString("pt-BR")}</span></h3><div class="profile-media-grid">${media}</div></section><section class="profile-section"><h3>Grupos em comum <span>${Number(profile.group_count).toLocaleString("pt-BR")}</span></h3><div class="common-groups">${groups}</div></section></section>`;
    body.querySelector(".profile-open-chat")?.addEventListener("click", () => {
      if (!profile.direct_chat_id) return;
      openChat({chat_id: profile.direct_chat_id, jid: profile.jid, name: profile.name});
      document.querySelector("#app").classList.remove("details-open");
    });
    body.querySelectorAll(".common-group").forEach((button) => button.addEventListener("click", () => {
      openChat({chat_id: Number(button.dataset.chatId), jid: button.dataset.jid, name: button.dataset.name});
      document.querySelector("#app").classList.remove("details-open");
    }));
  } catch (error) {
    body.innerHTML = '<div class="empty">Não foi possível carregar as informações desse contato.</div>';
  }
}

document.addEventListener("click", (event) => {
  const sender = event.target.closest(".message .sender");
  if (sender) {
    event.preventDefault(); event.stopPropagation();
    const messageId = sender.closest(".message")?.dataset.id;
    if (messageId) showContactProfile(`/api/messages/${messageId}/contact-profile`);
    return;
  }
  const participant = event.target.closest(".participant p");
  if (participant) {
    const jid = participant.textContent.match(/[0-9]+@(?:lid|s\.whatsapp\.net)/)?.[0];
    if (jid) { event.preventDefault(); showContactProfile(`/api/contact-profile?jid=${encodeURIComponent(jid)}`); }
    return;
  }
  const chatName = event.target.closest(".chat-row .chat-main h3");
  if (chatName && /\+\d{7,15}/.test(chatName.textContent)) {
    event.preventDefault(); event.stopPropagation();
    showContactProfile(`/api/chats/${chatName.closest(".chat-row").dataset.id}/contact-profile`);
    return;
  }
  const headerIdentity = event.target.closest("#chatHeader p");
  if (headerIdentity && !headerIdentity.textContent.includes("@g.us")) {
    const active = document.querySelector(".chat-row.active");
    if (active) { event.preventDefault(); showContactProfile(`/api/chats/${active.dataset.id}/contact-profile`); }
  }
}, true);
