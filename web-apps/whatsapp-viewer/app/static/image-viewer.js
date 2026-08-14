const imageViewer = document.createElement("dialog");
imageViewer.id = "imageViewer";
imageViewer.className = "image-viewer";
imageViewer.setAttribute("aria-label", "Visualizador de imagem");
imageViewer.innerHTML = '<button class="image-viewer-close" type="button" aria-label="Fechar imagem">×</button><div class="image-viewer-stage"><img alt="Imagem ampliada"></div>';
document.body.append(imageViewer);

function openImageViewer(source, alt) {
  const image = imageViewer.querySelector("img");
  image.src = source;
  image.alt = alt || "Imagem ampliada";
  imageViewer.showModal();
}

function closeImageViewer() {
  if (!imageViewer.open) return;
  imageViewer.close();
  imageViewer.querySelector("img").removeAttribute("src");
}

document.addEventListener("click", (event) => {
  const image = event.target.closest(".message .media-card img, .profile-media-grid img");
  if (!image) return;
  event.preventDefault();
  event.stopPropagation();
  openImageViewer(image.currentSrc || image.src, image.alt);
}, true);

imageViewer.querySelector(".image-viewer-close").addEventListener("click", closeImageViewer);
imageViewer.addEventListener("click", (event) => {
  if (event.target === imageViewer || event.target.classList.contains("image-viewer-stage")) closeImageViewer();
});
imageViewer.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeImageViewer();
});
