/* ============================================================
   Logika keranjang halaman Kasir (POS).
   Semua angka di sini hanya untuk tampilan — server tetap
   memvalidasi ulang harga, stok, dan bayar saat checkout.
   ============================================================ */
(function () {
  "use strict";

  // --- Data produk dari template ---
  var produkList = [];
  try {
    produkList = JSON.parse(document.getElementById("produk-data").textContent);
  } catch (e) {
    produkList = [];
  }
  var produkById = {};
  produkList.forEach(function (p) {
    produkById[p.id] = p;
  });

  // cart: { id: qty }
  var cart = {};

  // --- Elemen ---
  var elItems = document.getElementById("cart-items");
  var elEmpty = document.getElementById("cart-empty");
  var elSubtotal = document.getElementById("subtotal");
  var elTotal = document.getElementById("total");
  var elKembalian = document.getElementById("kembalian");
  var elDiskon = document.getElementById("diskon");
  var elBayar = document.getElementById("bayar");
  var elBtnBayar = document.getElementById("btn-bayar");
  var elError = document.getElementById("checkout-error");

  // --- Util format rupiah ---
  function rupiah(n) {
    n = Math.round(n || 0);
    return "Rp " + n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function clampInt(v) {
    v = parseInt(v, 10);
    return isNaN(v) || v < 0 ? 0 : v;
  }

  // --- Tanggal struk ---
  var elTanggal = document.getElementById("struk-tanggal");
  if (elTanggal) {
    var now = new Date();
    elTanggal.textContent = now.toLocaleDateString("id-ID", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }

  // --- Hitung total ---
  function subtotalCart() {
    var sum = 0;
    Object.keys(cart).forEach(function (id) {
      var p = produkById[id];
      if (p) sum += p.harga * cart[id];
    });
    return sum;
  }

  // --- Tambah / ubah qty ---
  function addToCart(id) {
    var p = produkById[id];
    if (!p) return;
    var current = cart[id] || 0;
    if (current + 1 > p.stok) {
      flashError("Stok " + p.nama + " hanya " + p.stok + ".");
      return;
    }
    cart[id] = current + 1;
    render();
  }

  function setQty(id, qty) {
    var p = produkById[id];
    if (!p) return;
    qty = clampInt(qty);
    if (qty <= 0) {
      delete cart[id];
    } else if (qty > p.stok) {
      cart[id] = p.stok;
      flashError("Stok " + p.nama + " hanya " + p.stok + ".");
    } else {
      cart[id] = qty;
    }
    render();
  }

  // --- Render keranjang ---
  function render() {
    var ids = Object.keys(cart);

    // daftar item
    if (ids.length === 0) {
      elItems.innerHTML = "";
      elItems.appendChild(elEmpty);
      elEmpty.classList.remove("hidden");
    } else {
      if (elEmpty.parentNode) elEmpty.parentNode.removeChild(elEmpty);
      var html = "";
      ids.forEach(function (id) {
        var p = produkById[id];
        var qty = cart[id];
        var sub = p.harga * qty;
        html +=
          '<div class="cart-item" data-id="' + id + '">' +
            '<div class="cart-item-row1">' +
              '<span class="cart-item-nama">' + escapeHtml(p.nama) + "</span>" +
              '<span class="leader"></span>' +
              '<span class="cart-item-sub mono">' + rupiah(sub) + "</span>" +
            "</div>" +
            '<div class="cart-item-row2">' +
              '<div class="qty-ctrl">' +
                '<button type="button" data-act="dec">−</button>' +
                '<span class="qty-val mono">' + qty + "</span>" +
                '<button type="button" data-act="inc">+</button>' +
              "</div>" +
              '<span class="cart-item-price mono">@ ' + rupiah(p.harga) + "</span>" +
              '<button type="button" class="cart-remove" data-act="del">hapus</button>' +
            "</div>" +
          "</div>";
      });
      elItems.innerHTML = html;
    }

    // total
    var subtotal = subtotalCart();
    var diskon = clampInt(elDiskon.value);
    if (diskon > subtotal) {
      diskon = subtotal;
      elDiskon.value = diskon;
    }
    var net = subtotal - diskon;
    elSubtotal.textContent = rupiah(subtotal);
    elTotal.textContent = rupiah(net);

    // kembalian
    var bayar = clampInt(elBayar.value);
    var kembali = bayar - net;
    elKembalian.textContent = rupiah(kembali > 0 ? kembali : 0);

    // tombol bayar aktif kalau ada item & bayar cukup
    var bisaBayar = ids.length > 0 && bayar >= net && net >= 0;
    elBtnBayar.disabled = !bisaBayar;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var errTimer = null;
  function flashError(msg) {
    elError.textContent = msg;
    elError.classList.remove("hidden");
    clearTimeout(errTimer);
    errTimer = setTimeout(function () {
      elError.classList.add("hidden");
    }, 3500);
  }

  // --- Event: klik tile produk ---
  document.getElementById("produk-grid").addEventListener("click", function (e) {
    var tile = e.target.closest(".produk-tile");
    if (!tile || tile.disabled) return;
    addToCart(tile.getAttribute("data-id"));
  });

  // --- Event: kontrol qty di keranjang ---
  elItems.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-act]");
    if (!btn) return;
    var row = e.target.closest(".cart-item");
    if (!row) return;
    var id = row.getAttribute("data-id");
    var act = btn.getAttribute("data-act");
    if (act === "inc") addToCart(id);
    else if (act === "dec") setQty(id, (cart[id] || 0) - 1);
    else if (act === "del") setQty(id, 0);
  });

  // --- Event: diskon & bayar ---
  elDiskon.addEventListener("input", render);
  elBayar.addEventListener("input", render);

  // --- Quick pay ---
  document.getElementById("quick-pay").addEventListener("click", function (e) {
    var btn = e.target.closest("button");
    if (!btn) return;
    if (btn.getAttribute("data-action") === "pas") {
      elBayar.value = subtotalCart() - clampInt(elDiskon.value);
    } else {
      elBayar.value = clampInt(btn.getAttribute("data-amount"));
    }
    render();
  });

  // --- Filter kategori & pencarian ---
  var kategoriAktif = "";
  var cariText = "";
  var chips = document.getElementById("chips");
  var inputCari = document.getElementById("cari-produk");
  var gridEmpty = document.getElementById("grid-empty");

  function applyFilter() {
    var tiles = document.querySelectorAll(".produk-tile");
    var terlihat = 0;
    tiles.forEach(function (t) {
      var kat = t.getAttribute("data-kategori");
      var nama = t.getAttribute("data-nama").toLowerCase();
      var cocokKat = !kategoriAktif || kat === kategoriAktif;
      var cocokCari = !cariText || nama.indexOf(cariText) !== -1;
      var show = cocokKat && cocokCari;
      t.style.display = show ? "" : "none";
      if (show) terlihat++;
    });
    gridEmpty.classList.toggle("hidden", terlihat > 0);
  }

  chips.addEventListener("click", function (e) {
    var chip = e.target.closest(".chip");
    if (!chip) return;
    chips.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
    chip.classList.add("active");
    kategoriAktif = chip.getAttribute("data-kategori");
    applyFilter();
  });

  inputCari.addEventListener("input", function () {
    cariText = this.value.trim().toLowerCase();
    applyFilter();
  });

  // --- Checkout ---
  elBtnBayar.addEventListener("click", function () {
    var ids = Object.keys(cart);
    if (ids.length === 0) return;

    var items = ids.map(function (id) {
      return { produk_id: parseInt(id, 10), qty: cart[id] };
    });
    var payload = {
      items: items,
      bayar: clampInt(elBayar.value),
      diskon: clampInt(elDiskon.value),
    };

    elBtnBayar.disabled = true;
    elBtnBayar.textContent = "Memproses…";

    fetch("/kasir/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (r) {
        if (r.ok && r.data.transaksi_id) {
          window.location = "/kasir/struk/" + r.data.transaksi_id;
        } else {
          flashError(r.data.error || "Checkout gagal.");
          elBtnBayar.disabled = false;
          elBtnBayar.textContent = "Bayar";
        }
      })
      .catch(function () {
        flashError("Tidak bisa terhubung ke server.");
        elBtnBayar.disabled = false;
        elBtnBayar.textContent = "Bayar";
      });
  });

  // render awal
  render();
})();
