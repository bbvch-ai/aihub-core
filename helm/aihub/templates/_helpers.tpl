
{{/*
Create a fully qualified app name with component.
Pattern: RELEASE_NAME-COMPONENT
Component is always required.
*/}}
{{- define "aihub.fullname" -}}
{{- $name := .context.Release.Name | trunc 63 | trimSuffix "-" }}
{{- if .context.Values.fullnameOverride }}
{{- $name = .context.Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- printf "%s-%s" $name .component }}
{{- end }}


{{/*
Common labels
*/}}
{{- define "aihub.labels" -}}
{{ include "aihub.selectorLabels" . }}
app.kubernetes.io/version: "0.1.0"
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "aihub.selectorLabels" -}}
app.kubernetes.io/name: {{ default "aihub" .Values.nameOverride | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}



{{/*
Common environment variables for all containers
*/}}
{{- define "aihub.commonEnv" -}}
- name: DOMAIN
  value: {{ .Values.global.domain | quote }}
- name: LOG_LEVEL
  value: {{ .Values.global.logLevel | quote }}
{{- end }}

{{/*
Simple image helpers - no more complex templating!
*/}}

{{/*
Common volume mounts for all containers
*/}}
{{- define "aihub.commonVolumeMounts" -}}
- name: env-config
  mountPath: /etc/env
  readOnly: true
{{- end }}


{{/*
Common security context
*/}}
{{- define "aihub.securityContext" -}}
{{- if .Values.securityContext }}
{{- toYaml .Values.securityContext }}
{{- else }}
runAsNonRoot: true
runAsUser: 1001
fsGroup: 1001
{{- end }}
{{- end }}

{{/*
Common pod security context
*/}}
{{- define "aihub.podSecurityContext" -}}
{{- if .Values.podSecurityContext }}
{{- toYaml .Values.podSecurityContext }}
{{- else }}
runAsNonRoot: true
runAsUser: 1001
fsGroup: 1001
seccompProfile:
  type: RuntimeDefault
{{- end }}
{{- end }}

{{/*
Global tolerations for all services
*/}}
{{- define "aihub.globalTolerations" -}}
{{- if .Values.global.tolerations }}
{{- toYaml .Values.global.tolerations }}
{{- end }}
{{- end }}
