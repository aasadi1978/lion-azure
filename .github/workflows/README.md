# Deployment approach through CI/CD

We're currently running a **regular Azure Web App (App Service)** that executes, e.g., a **Python application directly** on a **VM managed by Azure**, without containers.

### 🔍 To be precise:

- It's **not a full VM you control** — it's part of a **multi-tenant or dedicated App Service Plan**, where Azure:

  - Handles the **VM provisioning and OS patching**
  - Manages the **runtime environment** (Python, Node, .NET, etc.)
  - Provides **auto-scaling, monitoring, and load balancing**

Your app runs in a **sandboxed worker process** on this VM using the selected runtime.

---

### 🧰 Summary:

| Layer          | What You Have                                 |
| -------------- | --------------------------------------------- |
| Infrastructure | Azure-managed VM (part of App Service Plan)   |
| App Runtime    | Python 3.x (selected in App Service config)   |
| Deployment     | GitHub Actions (deploys code, not containers) |
| Hosting Model  | PaaS – Code-based (no Docker)                 |

---

This is a **simple, cost-effective, and scalable model** for many production apps. If you ever need more control (e.g., custom OS dependencies, private networking), we can look at containerizing or moving to Azure Container Apps or AKS.
