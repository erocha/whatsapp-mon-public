function linkifyMessage(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!node.parentElement.closest("a, audio, video, .meta, .sender") && /https?:\/\/[^\s<]+/i.test(node.nodeValue)) nodes.push(node);
  }
  for (const node of nodes) {
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    for (const match of node.nodeValue.matchAll(/https?:\/\/[^\s<]+/gi)) {
      let url = match[0], suffix = "";
      while (/[.,;:!?)]$/.test(url)) { suffix = url.slice(-1) + suffix; url = url.slice(0, -1); }
      fragment.append(node.nodeValue.slice(cursor, match.index));
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.className = "message-link";
      link.textContent = url;
      fragment.append(link, suffix);
      cursor = match.index + match[0].length;
    }
    fragment.append(node.nodeValue.slice(cursor));
    node.replaceWith(fragment);
  }
}

const messageContainer = document.querySelector("#messages");
new MutationObserver((records) => {
  for (const record of records) for (const node of record.addedNodes) {
    if (node.nodeType !== Node.ELEMENT_NODE) continue;
    if (node.matches?.(".message")) linkifyMessage(node);
    node.querySelectorAll?.(".message").forEach(linkifyMessage);
  }
}).observe(messageContainer, { childList: true, subtree: true });
