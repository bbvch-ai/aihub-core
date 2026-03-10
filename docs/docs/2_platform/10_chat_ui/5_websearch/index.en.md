---
title: Web search capability
---

# Web search capability

Agents can access web information to answer questions requiring current data beyond their training or internal knowledge
bases. Organizations control this through configuration.

Select "Web Search".

![Select Web Search](../../../../media/open_webui/select_web_search_button.jpeg)

Enter something you want to search for.

![Enter Search Query](../../../../media/open_webui/enter_search_query.jpeg)

The model will take some time coming up with a search query and then executing that search. After which it will output
what it found.

![Search Results](../../../../media/open_webui/search_results_displayed.jpeg)

The websites it retrieved the information from are listed as references.

![Search References](../../../../media/open_webui/search_references_citations.jpeg)

## Search configuration

Web search can be enabled or disabled per agent. Different policies apply to different use cases or user groups.

Each agent has independent web search configuration based on purpose and risk profile. Web search can be restricted to
specific user roles through role-based access control. Search capabilities can be modified at runtime without system
changes.

## Search restrictions

Organizations can limit searches to approved domains, trusted sources, or specific content types like academic
institutions or government websites.

Search queries can be validated, filtered, or transformed to ensure compliance with data protection policies and prevent
sensitive information leakage.

Retrieved web content can be validated against organizational standards before presentation.

Search restrictions can align with industry regulations, internal policies, or contractual obligations.

## Source attribution

When agents use web search, the system provides traceable attribution of external sources.

Users see clear distinctions between internal knowledge and external web sources. Web results appear as structured,
clickable citations with URLs, titles, and content previews. Users receive information about why specific sources were
retrieved.

Every search query, retrieved result, and user interaction is captured for audit purposes. The entire search process -
from query validation through result filtering to presentation - is traceable through the observability infrastructure.

## Use cases

Agents supplement internal knowledge with current market data, regulatory updates, industry news, or technical
documentation from external sources.

When internal knowledge bases have gaps, agents access external information while clearly attributing sources.

Agents can validate internal data against authoritative external sources.

Complex research tasks benefit from orchestration of both internal and external sources.

## Governance and security

Organizations can ensure that search queries don't expose sensitive information to external providers through query
validation and filtering.

Web content is validated against organizational standards before presentation, preventing inappropriate or unreliable
sources from reaching users.

The permission system allows control over which users or groups can use web search for which purposes.

Complete audit trails and transparent source attribution support compliance with data governance regulations and
industry standards.

Configurable restrictions and validation mechanisms let organizations balance the value of external information with
their risk tolerance and compliance obligations.
