"use strict";

const KINDS = ["claim", "assumption", "axiom", "evidence"];

let rebuildMode = false;
let pendingDelete = null;

/* ---------- talking to the API ---------- */

async function api(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch("/api" + path, options);
  if (!response.ok) {
    throw new Error(method + " " + path + " returned " + response.status);
  }
  return response.status === 204 ? null : response.json();
}

/* ---------- actions ---------- */

async function createNode(parentId) {
  const created = await api("POST", "/nodes", {
    text: "New claim",
    kind: "assumption",
    note: "",
    parent_id: parentId,
  });
  await load();
  const input = document.querySelector('input.text[data-id="' + created.id + '"]');
  if (input) {
    input.focus();
    input.select();
  }
}

async function patchNode(nodeId, changes) {
  await api("PATCH", "/nodes/" + nodeId, changes);
  await load();
}

async function deleteNode(nodeId) {
  await api("DELETE", "/nodes/" + nodeId);
  pendingDelete = null;
  await load();
}

/* ---------- rebuild mode ---------- */

function markGrounded(node) {
  const descendantGrounded = node.children
    .map(function (child) { return markGrounded(child); })
    .some(Boolean);
  node.grounded = node.kind === "axiom" || descendantGrounded;
  return node.grounded;
}

function countNodes(nodes) {
  return nodes.reduce(function (total, node) {
    return total + 1 + countNodes(node.children);
  }, 0);
}

/* ---------- drawing ---------- */

function renderNode(node) {
  const li = document.createElement("li");
  li.className = "node kind-" + node.kind;
  if (rebuildMode && !node.grounded) {
    li.classList.add("dim");
  }

  const row = document.createElement("div");
  row.className = "row";

  const kind = document.createElement("select");
  kind.className = "kind";
  KINDS.forEach(function (name) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    option.selected = name === node.kind;
    kind.appendChild(option);
  });
  kind.addEventListener("change", function () {
    patchNode(node.id, { kind: kind.value });
  });

  const text = document.createElement("input");
  text.className = "text";
  text.value = node.text;
  text.dataset.id = node.id;
  text.addEventListener("change", function () {
    const value = text.value.trim();
    if (value === "") {
      text.value = node.text;
      return;
    }
    patchNode(node.id, { text: value });
  });

  const add = document.createElement("button");
  add.textContent = "+";
  add.title = "Add a node underneath this one";
  add.addEventListener("click", function () {
    createNode(node.id);
  });

  const remove = document.createElement("button");
  remove.textContent = "×";
  remove.title = "Delete this node and everything under it";
  remove.addEventListener("click", function () {
    if (pendingDelete === node.id) {
      deleteNode(node.id);
      return;
    }
    pendingDelete = node.id;
    remove.textContent = "sure?";
    remove.classList.add("confirm");
    setTimeout(function () {
      if (pendingDelete === node.id) {
        pendingDelete = null;
        remove.textContent = "×";
        remove.classList.remove("confirm");
      }
    }, 2500);
  });

  row.append(kind, text, add, remove);

  const note = document.createElement("input");
  note.className = "note";
  note.placeholder = "why does this hold?";
  note.value = node.note;
  note.addEventListener("change", function () {
    patchNode(node.id, { note: note.value });
  });

  li.append(row, note);

  if (node.children.length > 0) {
    const children = document.createElement("ul");
    node.children.forEach(function (child) {
      children.appendChild(renderNode(child));
    });
    li.appendChild(children);
  }

  return li;
}

async function load() {
  const container = document.getElementById("tree");
  const errorBox = document.getElementById("error");

  let tree;
  try {
    tree = await api("GET", "/tree");
  } catch (error) {
    errorBox.textContent = "Could not reach the server: " + error.message;
    errorBox.style.display = "block";
    return;
  }
  errorBox.style.display = "none";

  tree.forEach(function (root) { markGrounded(root); });

  const roots = document.createElement("ul");
  roots.className = "roots";
  tree.forEach(function (node) {
    roots.appendChild(renderNode(node));
  });
  container.replaceChildren(roots);

  const total = countNodes(tree);
  document.getElementById("count").textContent =
    total === 0 ? "" : total + (total === 1 ? " node" : " nodes");
  document.getElementById("empty").style.display = total === 0 ? "block" : "none";
}

/* ---------- wiring ---------- */

document.getElementById("add-root").addEventListener("click", function () {
  createNode(null);
});

document.getElementById("rebuild").addEventListener("click", function (event) {
  rebuildMode = !rebuildMode;
  event.currentTarget.classList.toggle("active", rebuildMode);
  load();
});

load();
