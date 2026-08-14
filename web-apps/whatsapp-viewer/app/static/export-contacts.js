const logoutForm = document.querySelector("#logoutForm");
if (logoutForm) {
  const importBox = document.createElement("label");
  importBox.className = "file-field";
  importBox.innerHTML = 'Importar contatos CSV <small>Phone;Name;PushName;ShortName;IsBusiness</small><input id="contactsCsvInput" type="file" accept=".csv,text/csv">';
  logoutForm.before(importBox);
  importBox.querySelector("input").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    form.append("csrf_token", document.querySelector("#app").dataset.csrf);
    try {
      const response = await fetch("/api/import-contacts-csv", {method: "POST", body: form});
      if (response.status === 401) { location = "/login"; return; }
      if (!response.ok) throw new Error((await response.json()).detail || "Falha na importação");
      const result = await response.json();
      alert(`${result.imported.toLocaleString("pt-BR")} contatos importados; ${result.linked_lids.toLocaleString("pt-BR")} identificadores vinculados; ${result.skipped.toLocaleString("pt-BR")} registros sem telefone ignorados.`);
      if (typeof loadChats === "function") loadChats();
    } catch (error) { alert(error.message); }
    finally { event.target.value = ""; }
  });
  const exportBox = document.createElement("div");
  exportBox.className = "export-contacts";
  exportBox.innerHTML = '<a class="document" href="/api/export-vcf" download="whatsapp-conversas-diretas.vcf">⬇ <span>Exportar contatos das conversas diretas</span></a><a class="document" href="/api/export-vcf?scope=all" download="whatsapp-todos-participantes.vcf">⬇ <span>Exportar todos os participantes identificáveis</span></a><p class="muted">O segundo arquivo pode conter dezenas de milhares de números. Identificadores @lid sem telefone são ignorados.</p>';
  logoutForm.before(exportBox);
}
