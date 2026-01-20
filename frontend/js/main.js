// NOTE: 这是从 mymo/frontend/main.js 迁移过来的“单文件版本”。
// 现在拆到 frunk/frontend/js/ 下，后续可以继续按 login/toolbox/notes/koculator 再拆更细。

const { createApp, nextTick } = Vue;

const app = createApp({
  data() {
    return {
      api: "/api",
      user: null,
      view: "toolbox",
      tools: [],
      form: { email: "", password: "" },
      draft: { title: "", content: "", tag_ids: [] },
      notes: [],
      err: "",
      updateTimers: {},
      tags: [],
      searchQuery: "",
      selectedTagId: null,
      showTagManager: false,
      newTag: { name: "", color: "#007bff" },
      pagination: { page: 1, pages: 1, total: 0, per_page: 10 },
      editorInstances: {},
      draftEditor: null,
      tinymceReady: false,
      showNewMemoForm: false,
      calc: { expr: "", result: "", hasError: false },
    };
  },
  async mounted() {
    await this.waitForTinyMCE();

    try {
      const res = await this._get("/auth/me");
      if (res && res.user) {
        this.user = res.user;
        await this.refreshToolbox();
        this.goToolbox();
      }
    } catch (error) {
      console.log("用户未登录");
    }

    window.addEventListener("keydown", (e) => this.onCalcKeydown(e));
  },
  methods: {
    async refreshToolbox() {
      try {
        const res = await this._get("/tools/");
        this.tools = res.tools || [];
      } catch (e) {
        this.tools = [];
      }
    },
    goToolbox() {
      this.view = "toolbox";
    },
    async openTool(tool) {
      const view = tool?.entry?.view;
      if (!view) return;
      this.view = view;

      if (view === "notes") {
        await this.loadNotes();
        this.loadTags();
      }
      if (view === "koculator") {
        this.calc.hasError = false;
      }
    },

    async waitForTinyMCE() {
      let attempts = 0;
      while (typeof window.tinymce === "undefined" && attempts < 50) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
      }
      this.tinymceReady = typeof window.tinymce !== "undefined";
    },

    expandNewMemoForm() {
      this.showNewMemoForm = true;
      if (this.tinymceReady) {
        nextTick(() => this.initDraftEditor());
      }
    },
    cancelNewMemo() {
      this.showNewMemoForm = false;
      this.draft = { title: "", content: "", tag_ids: [] };
      const draftEditor = window.tinymce.get("draft-editor");
      if (draftEditor) {
        try {
          draftEditor.destroy();
        } catch {}
      }
      this.draftEditor = null;
    },

    startEdit(note) {
      note.isEditing = true;
      if (note.content && !this.isHtmlContent(note.content)) {
        note.content = this.textToHtml(note.content);
      }
      nextTick(() => this.initNoteEditor(note));
    },
    finishEdit(note) {
      const editorId = "note-editor-" + note.id;
      const editor = window.tinymce.get(editorId);
      if (editor) {
        note.content = editor.getContent();
        try {
          editor.destroy();
        } catch {}
      }
      note.isEditing = false;
      this.scheduleUpdate(note);
    },
    isHtmlContent(content) {
      return /<[^>]+>/.test(content);
    },
    textToHtml(text) {
      if (!text) return "";
      return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>")
        .replace(/^(.*)$/, "<p>$1</p>");
    },
    initDraftEditor() {
      if (!this.tinymceReady) return;
      const editorId = "draft-editor";
      const existingEditor = window.tinymce.get(editorId);
      if (existingEditor) existingEditor.destroy();
      if (this.draftEditor) {
        try {
          this.draftEditor.destroy();
        } catch {}
        this.draftEditor = null;
      }
      setTimeout(() => {
        window.tinymce.init({
          selector: "#" + editorId,
          height: 200,
          menubar: false,
          plugins: [
            "lists",
            "link",
            "image",
            "charmap",
            "preview",
            "searchreplace",
            "visualblocks",
            "code",
            "fullscreen",
            "insertdatetime",
            "media",
            "table",
            "help",
            "wordcount",
          ],
          toolbar:
            "undo redo | formatselect | bold italic underline | alignleft aligncenter alignright | bullist numlist | link image | code",
          content_style:
            "body { font-family: system-ui, -apple-system; font-size: 14px; line-height: 1.6; }",
          placeholder: "开始写你的笔记...",
          setup: (editor) => {
            this.draftEditor = editor;
            editor.on("change keyup", () => {
              this.draft.content = editor.getContent();
            });
            editor.on("init", () => {
              editor.setContent(this.draft.content || "");
            });
          },
        });
      }, 100);
    },
    initNoteEditor(note) {
      if (!this.tinymceReady) return;
      const editorId = "note-editor-" + note.id;
      const existingEditor = window.tinymce.get(editorId);
      if (existingEditor) existingEditor.destroy();
      setTimeout(() => {
        window.tinymce.init({
          selector: "#" + editorId,
          height: 150,
          menubar: false,
          plugins: ["lists", "link", "code", "autolink"],
          toolbar: "bold italic underline | bullist numlist | link | code",
          content_style:
            "body { font-family: system-ui, -apple-system; font-size: 14px; line-height: 1.5; }",
          placeholder: "笔记内容",
          setup: (editor) => {
            editor.on("change keyup", () => {
              note.content = editor.getContent();
              this.scheduleUpdate(note);
            });
            editor.on("init", () => editor.setContent(note.content || ""));
          },
        });
      }, 100);
    },

    async register() {
      this.err = "";
      await this._post("/auth/register", this.form).catch(
        (e) => (this.err = e.message)
      );
    },
    async login() {
      this.err = "";
      const res = await this._post("/auth/login", this.form).catch(
        (e) => (this.err = e.message)
      );
      if (res) {
        this.user = res.user;
        await this.refreshToolbox();
        this.goToolbox();
      }
    },
    async logout() {
      await this._post("/auth/logout", {});
      this.user = null;
      this.view = "toolbox";
      this.tools = [];
      this.notes = [];
      this.tags = [];
      this.searchQuery = "";
      this.selectedTagId = null;
      this.pagination = { page: 1, pages: 1, total: 0, per_page: 10 };
      this.calcClear();
    },

    async loadNotes() {
      let url = "/notes/";
      const params = new URLSearchParams();
      if (this.searchQuery) params.append("search", this.searchQuery);
      if (this.selectedTagId) params.append("tag_id", this.selectedTagId);
      params.append("page", this.pagination.page);
      params.append("per_page", this.pagination.per_page);
      if (params.toString()) url += "?" + params.toString();
      const response = await this._get(url);
      this.notes = (response.notes || []).map((note) => ({
        ...note,
        isEditing: false,
      }));
      this.pagination = {
        page: response.page,
        pages: response.pages,
        total: response.total,
        per_page: response.per_page,
      };
    },
    async createNote() {
      if (this.draftEditor) this.draft.content = this.draftEditor.getContent();
      if (!this.draft.title && this.isContentEmpty(this.draft.content)) return;
      await this._post("/notes/", this.draft);
      this.cancelNewMemo();
      this.pagination.page = 1;
      this.loadNotes();
      this.loadTags();
    },
    scheduleUpdate(note) {
      if (this.updateTimers[note.id]) clearTimeout(this.updateTimers[note.id]);
      this.updateTimers[note.id] = setTimeout(() => this.updateNote(note), 500);
    },
    async updateNote(n) {
      n.updating = true;
      try {
        const updateData = {
          title: n.title,
          content: n.content,
          tag_ids: n.tags.map((t) => t.id),
        };
        const response = await this._put("/notes/" + n.id, updateData);
        if (response.note) {
          n.updated_at = response.note.updated_at;
          n.tags = response.note.tags;
        }
        n.justSaved = true;
        setTimeout(() => (n.justSaved = false), 2000);
        this.loadTags();
      } finally {
        n.updating = false;
      }
    },
    async deleteNote(id) {
      if (!confirm("确定要删除这条笔记吗？")) return;
      await this._del("/notes/" + id);
      this.loadNotes();
      this.loadTags();
    },
    formatTime(timeStr) {
      const date = new Date(timeStr);
      if (isNaN(date.getTime())) return "时间无效";
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);
      if (diffMs < 0) return "刚刚";
      if (diffMins < 1) return "刚刚";
      if (diffMins < 60) return `${diffMins}分钟前`;
      if (diffHours < 24) return `${diffHours}小时前`;
      if (diffDays < 7) return `${diffDays}天前`;
      return date.toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    },
    getCurrentTime() {
      return new Date().toLocaleString("zh-CN");
    },
    stripHtml(html) {
      if (!html) return "";
      const tmp = document.createElement("div");
      tmp.innerHTML = html;
      return tmp.textContent || tmp.innerText || "";
    },
    isContentEmpty(content) {
      if (!content) return true;
      const plainText = this.stripHtml(content).trim();
      return plainText.length === 0;
    },

    async loadTags() {
      const tags = await this._get("/notes/tags");
      this.tags = tags.map((tag) => ({ ...tag, isEditing: false }));
    },
    async createTag() {
      if (!this.newTag.name.trim()) {
        this.err = "标签名不能为空";
        return;
      }
      await this._post("/notes/tags", this.newTag).catch(
        (e) => (this.err = e.message)
      );
      this.newTag = { name: "", color: "#007bff" };
      this.err = "";
      this.loadTags();
    },
    async deleteTag(tagId) {
      if (!confirm("确定要删除这个标签吗？删除后所有笔记的该标签也会被移除。"))
        return;
      await this._del("/notes/tags/" + tagId).catch((e) => (this.err = e.message));
      this.loadTags();
      this.loadNotes();
      if (this.selectedTagId === tagId) this.selectedTagId = null;
    },
    startEditTag(tag) {
      tag.isEditing = true;
      tag.editName = tag.name;
      tag.editColor = tag.color;
    },
    async saveTagEdit(tag) {
      const newName = tag.editName.trim();
      if (!newName) {
        this.err = "标签名不能为空";
        return;
      }
      const existingTag = this.tags.find((t) => t.id !== tag.id && t.name === newName);
      if (existingTag) {
        this.err = "标签名已存在";
        return;
      }
      await this._put("/notes/tags/" + tag.id, {
        name: newName,
        color: tag.editColor,
      }).catch((e) => (this.err = e.message));
      tag.name = newName;
      tag.color = tag.editColor;
      tag.isEditing = false;
      this.loadTags();
      this.loadNotes();
      this.err = "";
    },
    cancelTagEdit(tag) {
      tag.isEditing = false;
      delete tag.editName;
      delete tag.editColor;
    },
    toggleTagInDraft(tagId) {
      const index = this.draft.tag_ids.indexOf(tagId);
      if (index > -1) this.draft.tag_ids.splice(index, 1);
      else this.draft.tag_ids.push(tagId);
    },
    toggleTagInNote(note, tagId) {
      const noteTagIds = note.tags.map((t) => t.id);
      const index = noteTagIds.indexOf(tagId);
      if (index > -1) note.tags.splice(index, 1);
      else {
        const tag = this.tags.find((t) => t.id === tagId);
        if (tag) note.tags.push(tag);
      }
      this.updateNote(note);
    },
    async search() {
      this.pagination.page = 1;
      await this.loadNotes();
    },
    clearSearch() {
      this.searchQuery = "";
      this.selectedTagId = null;
      this.pagination.page = 1;
      this.loadNotes();
      this.loadTags();
    },
    filterByTag(tagId) {
      this.selectedTagId = this.selectedTagId === tagId ? null : tagId;
      this.pagination.page = 1;
      this.loadNotes();
    },
    async togglePin(note) {
      const response = await this._post(`/notes/${note.id}/toggle-pin`, {}).catch(
        (e) => (this.err = e.message)
      );
      if (response) {
        note.is_pinned = response.is_pinned;
        this.loadNotes();
      }
    },
    async goPage(page) {
      if (page >= 1 && page <= this.pagination.pages && page !== this.pagination.page) {
        this.pagination.page = page;
        await this.loadNotes();
      }
    },
    async goPrev() {
      if (this.pagination.page > 1) {
        this.pagination.page--;
        await this.loadNotes();
      }
    },
    async goNext() {
      if (this.pagination.page < this.pagination.pages) {
        this.pagination.page++;
        await this.loadNotes();
      }
    },
    getPageNumbers() {
      const current = this.pagination.page;
      const total = this.pagination.pages;
      const pages = [];
      if (total <= 7) {
        for (let i = 1; i <= total; i++) pages.push(i);
      } else {
        if (current <= 4) {
          for (let i = 1; i <= 5; i++) pages.push(i);
          pages.push("...");
          pages.push(total);
        } else if (current >= total - 3) {
          pages.push(1);
          pages.push("...");
          for (let i = total - 4; i <= total; i++) pages.push(i);
        } else {
          pages.push(1);
          pages.push("...");
          for (let i = current - 1; i <= current + 1; i++) pages.push(i);
          pages.push("...");
          pages.push(total);
        }
      }
      return pages;
    },

    async _get(p) {
      const r = await fetch(this.api + p, { credentials: "include" });
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    },
    async _post(p, data) {
      const r = await fetch(this.api + p, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!r.ok) throw new Error((await r.json()).error || "error");
      return r.json();
    },
    async _put(p, data) {
      const r = await fetch(this.api + p, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    },
    async _del(p) {
      const r = await fetch(this.api + p, {
        method: "DELETE",
        credentials: "include",
      });
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    },

    // Koculator
    calcClear() {
      this.calc.expr = "";
      this.calc.result = "";
      this.calc.hasError = false;
    },
    calcBackspace() {
      this.calc.expr = (this.calc.expr || "").slice(0, -1);
      this.calc.hasError = false;
    },
    calcAppend(v) {
      const expr = this.calc.expr || "";
      const operators = ["+", "-", "*", "/"];
      const last = expr[expr.length - 1];
      if (operators.includes(v)) {
        if (!expr && v !== "-") return;
        if (last === "(" && v !== "-") return;
        if (operators.includes(last)) {
          this.calc.expr = expr.slice(0, -1) + v;
          this.calc.hasError = false;
          return;
        }
      }
      if (v === ")") {
        if (!expr || operators.includes(last) || last === "(") return;
      }
      if (v === "(") {
        if (last && (/\d|\./.test(last) || last === ")")) return;
      }
      if (v === ".") {
        const lastNumber = (expr.match(/-?\d*\.?\d*$/) || [""])[0];
        if (lastNumber.includes(".")) return;
        if (lastNumber === "" || lastNumber === "-") this.calc.expr += "0";
      }
      this.calc.expr += v;
      this.calc.hasError = false;
    },
    async calcEquals() {
      const expr = (this.calc.expr || "").trim();
      if (!expr) return;
      try {
        const res = await this._post("/tools/koculator/calc", { expr });
        if (res.ok) {
          this.calc.result = String(res.result);
          this.calc.hasError = false;
        } else {
          this.calc.result = `Error: ${res.error}`;
          this.calc.hasError = true;
        }
      } catch {
        this.calc.result = "Network error";
        this.calc.hasError = true;
      }
    },
    onCalcKeydown(event) {
      if (this.view !== "koculator") return;
      const key = event.key;
      if (/\d/.test(key)) return void this.calcAppend(key);
      if (key === ".") return void this.calcAppend(".");
      if (key === "Backspace") return void this.calcBackspace();
      if (key === "Escape") return void this.calcClear();
      if (key === "Enter" || key === "=") return void this.calcEquals();
      if (["+", "-", "*", "/"].includes(key)) return void this.calcAppend(key);
      if (key === "(" || key === ")") return void this.calcAppend(key);
    },
  },
});

app.mount("#app");

