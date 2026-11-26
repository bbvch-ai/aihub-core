# LLM Cost Is Stated in CHF

## Context

Every LLM call's cost comes from the per-token, per-second or per-image prices written into the LiteLLM configuration:
the compose config variants in `infra/configs/litellm/` and the LiteLLM config of the Kubernetes chart. Three places
turn those prices into money: LiteLLM's spend log (and with it the Usage and Customer Usage views), the Hub's own cost
events (`LLMCostTracker`, read from LiteLLM's `/v1/model/info`), and Langfuse, whose model definitions the Hub registers
from the same prices.

None of these records a currency, and the labels disagree. The prices are copied from CHF price lists: Infomaniak's
price page and the usage stoney reports, and the providers invoice in CHF. Yet the Hub API documents its price fields as
USD, the Admin UI cost table labels the same numbers CHF, and LiteLLM's UI and Langfuse print a dollar sign in front of
them. Before cost per tenant is used for billing or budgets, an operator has to know which currency a figure is in
without asking.

## Decision Drivers

- **Match the invoices**\
  The providers bill in CHF. Figures in the same currency can be checked against an invoice line by line, with no
  exchange rate in between.
- **Prices stay copyable**\
  A price taken from a provider's CHF list goes into the config as it is. A conversion step would have to be repeated,
  and dated, for every price and every rate change.
- **Customers are billed in CHF**\
  Tenant figures from LiteLLM's Customer Usage view feed what customers are charged, so they should already be in the
  currency of that charge.
- **No component can be told its currency**\
  LiteLLM and Langfuse have no currency setting; their UIs always print "\$". Whatever is decided has to be stated
  around them, not configured in them.

## Decision

LLM cost on the platform is stated in CHF.

- Every price in the LiteLLM configuration is a CHF amount, taken from the provider's CHF price list or measured from
  its CHF usage report, and written as a plain number like today.
- The figures LiteLLM, the Hub's cost events and Langfuse derive from those prices are therefore CHF, including user and
  tenant budgets once they are set.
- Every label the platform controls says CHF: the descriptions of the Hub API's price and cost fields, the Admin UI and
  the documentation.
- LiteLLM's UI and Langfuse keep printing "\$". The cost-control documentation states that these are CHF amounts.

Converting the prices to USD at a fixed rate was rejected: it would make every figure differ from the invoices by the
movement of the rate since the conversion, and add a conversion step to every price change, for the sole benefit of
matching the "\$" those two UIs print.

## Consequences

### Positive

- A month of LiteLLM spend per model can be compared with the providers' invoices directly.
- Prices are maintained the way they are today: copied from the provider's list.
- One currency for prices, usage, budgets and what customers are charged.

### Trade-offs

- The dollar sign in LiteLLM's UI and in Langfuse is misleading, and only the documentation corrects it.
- Prices are not directly comparable with public price lists in USD.
- The Hub API's price field descriptions say USD and must be changed, which changes the OpenAPI schema and the generated
  SDK.
- A provider that ever invoices in another currency needs its prices converted when they are entered, with the rate and
  date written next to them.
