---
title: The Ecosystem Model
---

# The ecosystem model: How everyone benefits

The Swiss AI Hub exists because AI infrastructure shouldn't be a competitive differentiator. Basic capabilities like LLM
access, document processing, and RAG should be commodities, available to everyone. Swiss organizations should compete on
their domain expertise and business innovation, not on who can build better authentication systems or vector databases.

## The Swiss opportunity

Switzerland is a small country competing in a global economy dominated by tech giants. While Google, Microsoft, and
Amazon pour billions into AI infrastructure, Swiss companies individually lack the resources to match that investment.
The typical response would be to accept dependency on foreign platforms, but Switzerland has another option:
collaboration.

The same democratic principles that make Switzerland successful as a nation can transform how we approach AI. Instead of
each organization building redundant infrastructure, we can pool our efforts on the foundation while competing on the
application layer. This isn't about eliminating competition; it's about moving competition to where it creates value.

## Infrastructure as commodity

Consider what every organization building AI needs:

- Secure model access with cost controls
- Document processing and vector storage
- Authentication and user management
- Monitoring and observability
- Deployment and scaling patterns

These requirements are universal. A bank's authentication needs aren't fundamentally different from an insurance
company's. A pharmaceutical company's document processing challenges mirror those of a manufacturing firm. Yet today,
each organization either builds these capabilities separately or surrenders to a foreign platform.

The Swiss AI Hub makes this infrastructure a commodity. Deploy the platform once, and these problems are solved. Every
improvement to the core platform benefits every organization using it. When someone contributes better document parsing,
everyone's document processing improves. When someone adds a new security feature, everyone becomes more secure.

## The contribution dynamic

The Swiss AI Hub is entirely Apache 2.0 licensed - platform, SDK, agents, pipelines, and processes. This permissive
licensing creates natural collaboration incentives without forcing them.

**Shared infrastructure benefits everyone:** When organizations improve core infrastructure, sharing makes sense because
everyone benefits. A bank that adds better compliance logging helps every regulated industry. A healthcare provider that
improves PII handling helps everyone with privacy concerns. These contributions flow back naturally because better
shared infrastructure reduces everyone's costs.

**Strategic differentiation stays private:** Organizations keep their competitive advantages proprietary. The
customer-facing agent that embodies your unique business processes, your specialized data processing, your domain
expertise - these stay yours. Apache 2.0 doesn't require sharing anything back, so you're free to keep strategic
innovations private while benefiting from and contributing to shared infrastructure.

## Why licensing matters for AI infrastructure

Understanding software licensing is critical when building AI infrastructure. Many organizations make costly mistakes by
assuming that code on GitHub is automatically free to use - it's not.

### The GitHub misconception

**Seeing source code ≠ open source ≠ free to use.** GitHub hosts both open-source projects and proprietary software with
restrictive licenses. Being able to *view* or *download* code doesn't mean you're legally permitted to *use* it,
especially in production or commercial contexts.

Example: **n8n**, one of the most popular workflow automation tools on GitHub, uses the "Sustainable Use License" (not
an open-source license). While you can download and run it, the license prohibits commercial use without purchasing an
enterprise license - even if you self-host. Many organizations discover this too late, after building dependencies on
these tools.

### License categories explained

**Permissive licenses** (MIT, Apache 2.0, BSD): Grant broad freedoms - use, modify, distribute commercially, keep
modifications private. No strings attached. These are ideal for building business infrastructure.

**Copyleft licenses** (GPL, AGPL): Require that any modifications or derivative works be released under the same
license. If you build on GPL software and distribute it, you must open-source your entire application. **AGPL extends
this to network use** - even offering the software as a service triggers the requirement. Dangerous for proprietary AI
products.

**Source-available licenses** (Elastic License, BSL, SSPL, "Sustainable Use"): Let you view and sometimes use the code,
but impose severe restrictions - often prohibiting commercial use, managed services, or competing products. Not
open-source despite appearing on GitHub.

**Proprietary/Custom licenses**: Vary widely. Require careful legal review. Often prohibit production use without
payment.

### Licenses to avoid in AI infrastructure

For production AI systems, be extremely cautious with:

- **AGPL/GPL**: Force your entire system open-source if you modify and distribute the software
- **SSPL (Server Side Public License)**: MongoDB's attempt to prevent cloud providers from offering managed versions;
  triggers open-source requirements for infrastructure
- **Elastic License v2**: Prohibits offering the software as a competing service
- **Business Source License (BSL)**: Time-delayed open source; restrictive until expiration date
- **Custom "source-available" licenses**: Usually prohibit commercial use or have unclear terms

These licenses might seem acceptable initially, but create legal landmines when you scale, offer services, or integrate
with customer systems.

### Our licensing commitment

The Swiss AI Hub rigorously evaluates every dependency - all 232 Python packages, 197 Node.js packages, and 28 external
Docker images. We verify that every component uses permissive licenses (MIT, Apache 2.0, BSD) or has been explicitly
reviewed and approved.

**You get complete freedom:** Use the entire stack commercially, modify anything, integrate with proprietary systems,
offer it as a service, or build products on top - without license conflicts, hidden restrictions, or future surprises.

**Why Apache 2.0 specifically:** Beyond being permissive, Apache 2.0 includes explicit patent grants, protecting you
from patent claims by contributors. It's trusted by enterprises, well-understood by legal teams, and compatible with
virtually all other licenses. It's the gold standard for collaborative infrastructure.

This isn't just idealism - it's pragmatism. Permissive licensing removes barriers to adoption, prevents vendor lock-in,
and ensures you own your AI infrastructure completely. No license audits, no compliance risks, no sudden rule changes.

## Real collaboration patterns

The ecosystem already shows how this works:

**Shared components:** Common agents for document summarization, question answering, and data extraction become
community assets. Every organization needs these basics, so sharing makes sense.

**Industry solutions:** Healthcare organizations collaborate on medical document processing. Financial services share
compliance-focused agents. These industry-specific solutions emerge naturally when organizations realize their
competitors abroad, not domestically, are the real threat.

**Infrastructure improvements:** Performance optimizations, security enhancements, and operational tools flow back to
the platform. Everyone benefits from a faster, more secure, more reliable foundation.

**Knowledge sharing:** Organizations share deployment patterns, best practices, and lessons learned. The same platform
means solutions are transferable.

## Where competition belongs

The ecosystem model doesn't eliminate competition; it focuses it where it matters:

**Your domain expertise** remains yours. The platform doesn't know your business rules, your customer relationships, or
your market insights. These create competitive advantage.

**Your specialized agents** reflect your unique processes and knowledge. While you might share generic document
processing, your customer service agent embodies your specific approach.

**Your data and training** remain proprietary. The platform provides tools to process and query your data, but the data
itself and the insights derived from it are your competitive moat.

**Your business innovation** is where competition should be. Instead of competing on who has better vector databases,
compete on who uses AI more creatively to serve customers.

## The network effect

As more organizations adopt the Swiss AI Hub, the ecosystem strengthens:

**Development accelerates** because common patterns emerge and get encoded into the SDK. What took weeks to build
becomes a configuration option.

**Quality improves** through collective debugging and testing. With many organizations running the same platform, edge
cases get discovered and fixed quickly.

**Costs decrease** through shared investment. Instead of each organization paying for complete development, costs are
distributed across the ecosystem.

**Innovation increases** because developers can build on a higher foundation. Instead of reimplementing basics, they can
explore new capabilities.

## The Swiss AI advantage

This collaborative approach gives Swiss organizations collective advantages:

**Speed:** New organizations can deploy production AI in days, not months, by leveraging existing work.

**Sovereignty:** Swiss data stays in Switzerland, processed by Swiss-controlled infrastructure, governed by Swiss law.

**Independence:** No single vendor controls the platform. No foreign company can change terms or cut access.

**Quality:** Collective investment produces better infrastructure than any single organization could build.

**Innovation:** Freed from infrastructure concerns, organizations focus on business innovation where real value lies.

## Making collaboration work

The ecosystem succeeds because it aligns incentives correctly:

Organizations contribute to infrastructure because they benefit directly from improvements. They share
non-differentiating capabilities because collaboration is more valuable than secrecy. They keep strategic innovations
private because Apache 2.0 permits both approaches - the choice is always yours.

The Swiss AI Hub provides the technical foundation for this collaboration, but the ecosystem is built by its members.
Every organization that deploys the platform, contributes improvements, or shares knowledge strengthens Swiss AI
capabilities collectively.

This is how Switzerland competes globally: not through individual organizations trying to match Big Tech resources, but
through collaborative infrastructure that lets every organization focus on what makes them unique. The platform is the
commodity layer that makes innovation possible.
