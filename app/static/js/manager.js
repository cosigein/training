// Manager Portal JS
// Lógica compartida entre páginas (complementa los scripts inline de cada template)
console.log('[Manager] Portal cargado');
document.addEventListener("DOMContentLoaded", function () {
  const modal = document.getElementById("mgrModal");
  const chip = document.getElementById("mgrChip");

  chip.onclick = function () {
    if (modal.style.display === "block") {
      modal.classList.remove("mgr-modal-div--open")
      modal.classList.add('mgr-modal-div--close');
      modal.addEventListener('animationend', function handler() {
        modal.classList.remove('mgr-modal-div--close');
        modal.style.display = 'none';
        modal.removeEventListener('animationend', handler);
      });
    } else {
      modal.style.display = "block";
      modal.classList.add("mgr-modal-div--open")
    }
  };
});