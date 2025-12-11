// OPEN SNAPSHOT MODAL
function openSnapshotModal(src) {
    if (!src) return;

    const modal = document.getElementById("snapshotModal");
    const content = document.getElementById("snapshotContent");

    document.getElementById("snapshotModalImg").src = src;

    modal.classList.remove("hidden");
    setTimeout(() => {
        modal.style.opacity = "1";
        content.style.transform = "scale(1)";
    }, 10);
}

// CLOSE SNAPSHOT MODAL
function closeSnapshotModal() {
    const modal = document.getElementById("snapshotModal");
    const content = document.getElementById("snapshotContent");

    modal.style.opacity = "0";
    content.style.transform = "scale(0.9)";

    setTimeout(() => {
        modal.classList.add("hidden");
    }, 250);
}

// CLOSE ON BACKGROUND CLICK
document.addEventListener("click", function(e) {
    const modal = document.getElementById("snapshotModal");
    if (e.target === modal) closeSnapshotModal();
});

// CLOSE ON ESC KEY
document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") closeSnapshotModal();
});
