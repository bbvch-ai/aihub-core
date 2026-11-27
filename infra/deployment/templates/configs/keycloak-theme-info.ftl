<#-- Keycloak's base info.ftl, except that a page Keycloak would leave without a link offers one to AI Hub.
     Admin-console invitations name no application, so Keycloak sets skipLink and the invitee is stranded.
     A Keycloak serving several AI Hubs (one realm each) names each realm's address as aihubUrl.<realm>. -->
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        <#if messageHeader??>
            ${kcSanitize(msg("${messageHeader}"))?no_esc}
        <#else>
            ${message.summary}
        </#if>
    <#elseif section = "form">
    <#assign aihubUrl = properties["aihubUrl." + realm.name]!properties.aihubUrl!"">
    <div id="kc-info-message">
        <p class="instruction">${message.summary}<#if requiredActions??><#list requiredActions>: <b><#items as reqActionItem>${kcSanitize(msg("requiredAction.${reqActionItem}"))?no_esc}<#sep>, </#items></b></#list><#else></#if></p>
        <#if !skipLink?? && pageRedirectUri?has_content>
            <p><a href="${pageRedirectUri}">${msg("backToApplication")}</a></p>
        <#elseif !skipLink?? && actionUri?has_content>
            <p><a href="${actionUri}">${msg("proceedWithAction")}</a></p>
        <#elseif !skipLink?? && (client.baseUrl)?has_content>
            <p><a href="${client.baseUrl}">${msg("backToApplication")}</a></p>
        <#elseif aihubUrl?has_content>
            <p><a id="aihub-link" href="${aihubUrl}">${msg("aihubGoToApp")}</a></p>
        </#if>
    </div>
    </#if>
</@layout.registrationLayout>
