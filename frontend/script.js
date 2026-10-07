// ---------- Config ----------
const API_BASE = window.location.origin; // same origin when served by FastAPI
const THREAD_ID = "web-" + (localStorage.getItem("ai_thread") || Math.random().toString(36).slice(2, 10));
localStorage.setItem("ai_thread", THREAD_ID.replace("web-", ""));

// ---------- DOM refs ----------
const form = document.getElementById("record-form");
const nameInput = document.getElementById("full-name");
const rollInput = document.getElementById("roll-number");
const ageInput = document.getElementById("age");
const emailInput = document.getElementById("email");
const recordsBody = document.getElementById("records-body");
const messageBox = document.getElementById("message");

const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatReset = document.getElementById("chat-reset");
const chatStatus = document.getElementById("chat-status");

let editingId = null;

// ---------- Helpers ----------
function showMessage(text, type) {
  messageBox.textContent = text;
  messageBox.className = "message " + type;
}

function clearMessage() {
  messageBox.textContent = "";
  messageBox.className = "message";
}

function createButton(text, className, onClick) {
  const button = document.createElement("button");
  button.textContent = text;
  button.className = "btn " + className;
  button.type = "button";
  button.addEventListener("click", onClick);
  return button;
}

function appendChat(role, text) {
  const div = document.createElement("div");
  div.className = "chat-msg " + role;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function setChatStatus(text, type) {
  chatStatus.textContent = text || "";
  chatStatus.className = "message " + (type || "");
}

// ---------- API helpers ----------
async function api(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.detail;
    let msg = "Request failed";
    if (typeof detail === "string") msg = detail;
    else if (Array.isArray(detail)) msg = detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    else if (detail) msg = JSON.stringify(detail);
    throw new Error(msg);
  }
  return data;
}

// ---------- READ ----------
async function loadRecords() {
  try {
    const students = await api("GET", "/students");
    renderTable(students);
  } catch (err) {
    showMessage("Failed to load students: " + err.message, "error");
    renderTable([]);
  }
}

function renderTable(records) {
  recordsBody.innerHTML = "";

  if (!records || records.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCell = document.createElement("td");
    emptyCell.colSpan = 6;
    emptyCell.className = "empty-row";
    emptyCell.textContent = "No records found. Add a student above or ask the AI.";
    emptyRow.appendChild(emptyCell);
    recordsBody.appendChild(emptyRow);
    return;
  }

  records.forEach(function (record) {
    const row = document.createElement("tr");

    if (editingId === record.id) {
      // Edit mode
      const idCell = document.createElement("td");
      idCell.textContent = record.id;

      const nameCell = document.createElement("td");
      const nameEd = document.createElement("input");
      nameEd.type = "text";
      nameEd.value = record.name;
      nameCell.appendChild(nameEd);

      const rollCell = document.createElement("td");
      const rollEd = document.createElement("input");
      rollEd.type = "number";
      rollEd.value = record.roll_number;
      rollCell.appendChild(rollEd);

      const ageCell = document.createElement("td");
      const ageEd = document.createElement("input");
      ageEd.type = "number";
      ageEd.value = record.age;
      ageCell.appendChild(ageEd);

      const emailCell = document.createElement("td");
      const emailEd = document.createElement("input");
      emailEd.type = "email";
      emailEd.value = record.email;
      emailCell.appendChild(emailEd);

      const actionsCell = document.createElement("td");
      actionsCell.className = "actions";
      actionsCell.appendChild(
        createButton("Save", "btn-save", function () {
          updateRecord(record.id, {
            name: nameEd.value.trim(),
            roll_number: parseInt(rollEd.value, 10),
            age: parseInt(ageEd.value, 10),
            email: emailEd.value.trim(),
          });
        })
      );
      actionsCell.appendChild(
        createButton("Cancel", "btn-cancel", function () {
          editingId = null;
          loadRecords();
        })
      );

      row.appendChild(idCell);
      row.appendChild(nameCell);
      row.appendChild(rollCell);
      row.appendChild(ageCell);
      row.appendChild(emailCell);
      row.appendChild(actionsCell);
    } else {
      const idCell = document.createElement("td");
      idCell.textContent = record.id;

      const nameCell = document.createElement("td");
      nameCell.textContent = record.name;

      const rollCell = document.createElement("td");
      rollCell.textContent = record.roll_number;

      const ageCell = document.createElement("td");
      ageCell.textContent = record.age;

      const emailCell = document.createElement("td");
      emailCell.textContent = record.email;

      const actionsCell = document.createElement("td");
      actionsCell.className = "actions";
      actionsCell.appendChild(
        createButton("Edit", "btn-edit", function () {
          editingId = record.id;
          renderTable(records);
        })
      );
      actionsCell.appendChild(
        createButton("Delete", "btn-delete", function () {
          deleteRecord(record.id);
        })
      );

      row.appendChild(idCell);
      row.appendChild(nameCell);
      row.appendChild(rollCell);
      row.appendChild(ageCell);
      row.appendChild(emailCell);
      row.appendChild(actionsCell);
    }

    recordsBody.appendChild(row);
  });
}

// ---------- CREATE ----------
form.addEventListener("submit", async function (event) {
  event.preventDefault();
  clearMessage();

  const payload = {
    name: nameInput.value.trim(),
    roll_number: parseInt(rollInput.value, 10),
    age: parseInt(ageInput.value, 10),
    email: emailInput.value.trim(),
  };

  if (!payload.name || !payload.roll_number || !payload.age || !payload.email) {
    showMessage("Please fill in all fields.", "error");
    return;
  }

  try {
    await api("POST", "/students", payload);
    form.reset();
    nameInput.focus();
    showMessage("Record added successfully.", "success");
    await loadRecords();
  } catch (err) {
    showMessage(err.message, "error");
  }
});

// ---------- UPDATE ----------
async function updateRecord(id, data) {
  try {
    await api("PUT", "/students/" + id, data);
    editingId = null;
    showMessage("Record updated successfully.", "success");
    await loadRecords();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ---------- DELETE ----------
async function deleteRecord(id) {
  if (!confirm("Are you sure you want to delete this record?")) return;
  try {
    await api("DELETE", "/students/" + id);
    if (editingId === id) editingId = null;
    showMessage("Record deleted.", "success");
    await loadRecords();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

// ---------- AI Chat ----------
chatForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const text = chatInput.value.trim();

  if (!text) return;

  appendChat("user", text);

  chatInput.value = "";
  chatSend.disabled = true;

  setChatStatus("Thinking…");

  try {
    const data = await api("POST", "/ai/chat", {
      message: text,
      thread_id: THREAD_ID,
    });

    // Show AI response
    appendChat("assistant", data.response);

    // Update status
    if (data.needs_clarification) {
      setChatStatus("Needs more information");
    } else {
      setChatStatus("Done", "success");
    }

    // IMPORTANT:
    // Always refresh the table after a successful AI request.
    // The backend may have created, updated, or deleted a student.
    await loadRecords();

  } catch (err) {

    appendChat(
      "system",
      "Error: " + err.message
    );

    setChatStatus(
      err.message,
      "error"
    );

  } finally {

    chatSend.disabled = false;
    chatInput.focus();
  }
});

chatReset.addEventListener("click", async function () {
  try {
    await api("POST", "/ai/reset?thread_id=" + encodeURIComponent(THREAD_ID));
    chatWindow.innerHTML = "";
    appendChat("system", "Conversation reset. How can I help?");
    setChatStatus("");
  } catch (err) {
    setChatStatus(err.message, "error");
  }
});

// ---------- Init ----------
appendChat("system", "AI ready. Ask me to create, list, find, update, or delete students.");
loadRecords();


// ```javascript
// // ============================================================
// // CONFIG
// // ============================================================

// const API_BASE = window.location.origin;

// const savedThread = localStorage.getItem("ai_thread");

// const THREAD_ID =
//   "web-" +
//   (savedThread || Math.random().toString(36).slice(2, 10));

// localStorage.setItem(
//   "ai_thread",
//   THREAD_ID.replace("web-", "")
// );


// // ============================================================
// // DOM REFERENCES
// // ============================================================

// const form = document.getElementById("record-form");

// const nameInput = document.getElementById("full-name");
// const rollInput = document.getElementById("roll-number");
// const ageInput = document.getElementById("age");
// const emailInput = document.getElementById("email");

// const recordsBody = document.getElementById("records-body");
// const messageBox = document.getElementById("message");

// const chatWindow = document.getElementById("chat-window");
// const chatForm = document.getElementById("chat-form");
// const chatInput = document.getElementById("chat-input");
// const chatSend = document.getElementById("chat-send");
// const chatReset = document.getElementById("chat-reset");
// const chatStatus = document.getElementById("chat-status");

// let editingId = null;


// // ============================================================
// // GENERAL HELPERS
// // ============================================================

// function showMessage(text, type) {
//   messageBox.textContent = text;
//   messageBox.className = "message " + (type || "");
// }


// function clearMessage() {
//   messageBox.textContent = "";
//   messageBox.className = "message";
// }


// function appendChat(role, text) {
//   const div = document.createElement("div");

//   div.className = "chat-msg " + role;
//   div.textContent = text;

//   chatWindow.appendChild(div);

//   chatWindow.scrollTop = chatWindow.scrollHeight;
// }


// function setChatStatus(text, type) {
//   chatStatus.textContent = text || "";
//   chatStatus.className = "message " + (type || "");
// }


// function createButton(text, className, onClick) {
//   const button = document.createElement("button");

//   button.type = "button";
//   button.textContent = text;
//   button.className = "btn " + className;

//   button.addEventListener("click", onClick);

//   return button;
// }


// // ============================================================
// // API
// // ============================================================

// async function api(method, path, body) {
//   const options = {
//     method: method,
//     headers: {
//       "Content-Type": "application/json"
//     }
//   };

//   if (body !== undefined) {
//     options.body = JSON.stringify(body);
//   }

//   const response = await fetch(API_BASE + path, options);

//   const data = await response.json().catch(function () {
//     return {};
//   });

//   if (!response.ok) {
//     const detail = data.detail;

//     let message = "Request failed";

//     if (typeof detail === "string") {
//       message = detail;
//     } else if (Array.isArray(detail)) {
//       message = detail
//         .map(function (item) {
//           return item.msg || JSON.stringify(item);
//         })
//         .join("; ");
//     } else if (detail) {
//       message = JSON.stringify(detail);
//     }

//     throw new Error(message);
//   }

//   return data;
// }


// // ============================================================
// // LOAD RECORDS
// // ============================================================

// async function loadRecords() {
//   try {
//     /*
//      * The timestamp prevents browser caching.
//      */
//     const students = await api(
//       "GET",
//       "/students?_=" + Date.now()
//     );

//     console.log("Latest students:", students);

//     renderTable(students);
//   } catch (error) {
//     console.error("Load records error:", error);

//     showMessage(
//       "Failed to load students: " + error.message,
//       "error"
//     );

//     renderTable([]);
//   }
// }


// // ============================================================
// // RENDER TABLE
// // ============================================================

// function renderTable(records) {
//   recordsBody.innerHTML = "";

//   if (!Array.isArray(records) || records.length === 0) {
//     const row = document.createElement("tr");
//     const cell = document.createElement("td");

//     cell.colSpan = 6;
//     cell.className = "empty-row";
//     cell.textContent =
//       "No records found. Add a student above or ask the AI.";

//     row.appendChild(cell);
//     recordsBody.appendChild(row);

//     return;
//   }

//   records.forEach(function (record) {
//     const row = document.createElement("tr");

//     // ========================================================
//     // EDIT MODE
//     // ========================================================

//     if (editingId === record.id) {
//       const idCell = document.createElement("td");
//       idCell.textContent = record.id;

//       const nameCell = document.createElement("td");
//       const nameEdit = document.createElement("input");

//       nameEdit.type = "text";
//       nameEdit.value = record.name;

//       nameCell.appendChild(nameEdit);


//       const rollCell = document.createElement("td");
//       const rollEdit = document.createElement("input");

//       rollEdit.type = "number";
//       rollEdit.value = record.roll_number;

//       rollCell.appendChild(rollEdit);


//       const ageCell = document.createElement("td");
//       const ageEdit = document.createElement("input");

//       ageEdit.type = "number";
//       ageEdit.value = record.age;

//       ageCell.appendChild(ageEdit);


//       const emailCell = document.createElement("td");
//       const emailEdit = document.createElement("input");

//       emailEdit.type = "email";
//       emailEdit.value = record.email;

//       emailCell.appendChild(emailEdit);


//       const actionsCell = document.createElement("td");
//       actionsCell.className = "actions";


//       actionsCell.appendChild(
//         createButton(
//           "Save",
//           "btn-save",
//           function () {
//             updateRecord(record.id, {
//               name: nameEdit.value.trim(),
//               roll_number: parseInt(
//                 rollEdit.value,
//                 10
//               ),
//               age: parseInt(
//                 ageEdit.value,
//                 10
//               ),
//               email: emailEdit.value.trim()
//             });
//           }
//         )
//       );


//       actionsCell.appendChild(
//         createButton(
//           "Cancel",
//           "btn-cancel",
//           function () {
//             editingId = null;
//             loadRecords();
//           }
//         )
//       );


//       row.appendChild(idCell);
//       row.appendChild(nameCell);
//       row.appendChild(rollCell);
//       row.appendChild(ageCell);
//       row.appendChild(emailCell);
//       row.appendChild(actionsCell);

//     } else {

//       // ======================================================
//       // NORMAL MODE
//       // ======================================================

//       const idCell = document.createElement("td");
//       idCell.textContent = record.id;


//       const nameCell = document.createElement("td");
//       nameCell.textContent = record.name;


//       const rollCell = document.createElement("td");
//       rollCell.textContent = record.roll_number;


//       const ageCell = document.createElement("td");
//       ageCell.textContent = record.age;


//       const emailCell = document.createElement("td");
//       emailCell.textContent = record.email;


//       const actionsCell = document.createElement("td");
//       actionsCell.className = "actions";


//       actionsCell.appendChild(
//         createButton(
//           "Edit",
//           "btn-edit",
//           function () {
//             editingId = record.id;
//             renderTable(records);
//           }
//         )
//       );


//       actionsCell.appendChild(
//         createButton(
//           "Delete",
//           "btn-delete",
//           function () {
//             deleteRecord(record.id);
//           }
//         )
//       );


//       row.appendChild(idCell);
//       row.appendChild(nameCell);
//       row.appendChild(rollCell);
//       row.appendChild(ageCell);
//       row.appendChild(emailCell);
//       row.appendChild(actionsCell);
//     }

//     recordsBody.appendChild(row);
//   });
// }


// // ============================================================
// // MANUAL CREATE
// // ============================================================

// form.addEventListener("submit", async function (event) {
//   event.preventDefault();

//   clearMessage();

//   const payload = {
//     name: nameInput.value.trim(),

//     roll_number: parseInt(
//       rollInput.value,
//       10
//     ),

//     age: parseInt(
//       ageInput.value,
//       10
//     ),

//     email: emailInput.value.trim()
//   };


//   if (
//     !payload.name ||
//     !payload.roll_number ||
//     !payload.age ||
//     !payload.email
//   ) {
//     showMessage(
//       "Please fill in all fields.",
//       "error"
//     );

//     return;
//   }


//   try {
//     await api(
//       "POST",
//       "/students",
//       payload
//     );

//     form.reset();

//     nameInput.focus();

//     showMessage(
//       "Record added successfully.",
//       "success"
//     );

//     await loadRecords();

//   } catch (error) {
//     showMessage(
//       error.message,
//       "error"
//     );
//   }
// });


// // ============================================================
// // MANUAL UPDATE
// // ============================================================

// async function updateRecord(id, data) {
//   try {
//     await api(
//       "PUT",
//       "/students/" + id,
//       data
//     );

//     editingId = null;

//     showMessage(
//       "Record updated successfully.",
//       "success"
//     );

//     await loadRecords();

//   } catch (error) {
//     showMessage(
//       error.message,
//       "error"
//     );
//   }
// }


// // ============================================================
// // MANUAL DELETE
// // ============================================================

// async function deleteRecord(id) {
//   const confirmed = window.confirm(
//     "Are you sure you want to delete this record?"
//   );

//   if (!confirmed) {
//     return;
//   }


//   try {
//     await api(
//       "DELETE",
//       "/students/" + id
//     );

//     if (editingId === id) {
//       editingId = null;
//     }

//     showMessage(
//       "Record deleted.",
//       "success"
//     );

//     await loadRecords();

//   } catch (error) {
//     showMessage(
//       error.message,
//       "error"
//     );
//   }
// }


// // ============================================================
// // AI CHAT
// // ============================================================

// chatForm.addEventListener("submit", async function (event) {
//   event.preventDefault();

//   const text = chatInput.value.trim();

//   if (!text) {
//     return;
//   }


//   // Show user's message
//   appendChat(
//     "user",
//     text
//   );


//   // Clear input
//   chatInput.value = "";


//   // Disable send button
//   chatSend.disabled = true;


//   setChatStatus(
//     "Thinking..."
//   );


//   try {
//     const data = await api(
//       "POST",
//       "/ai/chat",
//       {
//         message: text,
//         thread_id: THREAD_ID
//       }
//     );


//     console.log(
//       "AI response:",
//       data
//     );


//     // Show AI response
//     appendChat(
//       "assistant",
//       data.response
//     );


//     // Status
//     if (data.needs_clarification) {
//       setChatStatus(
//         "Needs more information"
//       );
//     } else {
//       setChatStatus(
//         "Done",
//         "success"
//       );
//     }


//     /*
//      * IMPORTANT:
//      *
//      * After the AI request finishes,
//      * fetch the database again.
//      */
//     await loadRecords();

//   } catch (error) {

//     console.error(
//       "AI request error:",
//       error
//     );


//     appendChat(
//       "system",
//       "Error: " + error.message
//     );


//     setChatStatus(
//       error.message,
//       "error"
//     );

//   } finally {

//     chatSend.disabled = false;

//     chatInput.focus();
//   }
// });


// // ============================================================
// // RESET AI
// // ============================================================

// chatReset.addEventListener("click", async function () {
//   try {

//     await api(
//       "POST",
//       "/ai/reset?thread_id=" +
//         encodeURIComponent(THREAD_ID)
//     );


//     chatWindow.innerHTML = "";


//     appendChat(
//       "system",
//       "Conversation reset. How can I help?"
//     );


//     setChatStatus("");

//   } catch (error) {

//     setChatStatus(
//       error.message,
//       "error"
//     );
//   }
// });


// // ============================================================
// // INITIALIZATION
// // ============================================================

// appendChat(
//   "system",
//   "AI ready. Ask me to create, list, find, update, or delete students."
// );

// loadRecords();
// ```
