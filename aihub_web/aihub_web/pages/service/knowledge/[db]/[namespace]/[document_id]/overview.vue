<template>
  <StructuralColumn
    :title="document?.document_title"
    :close-route="`/service/knowledge/${route.params.db}/${route.params.namespace}`"
    :loading="documentIsLoading"
  >
    <ConfirmDialog />
    <div class="mt-16 rounded-3xl border border-surface-100 p-9 shadow-lg dark:border-surface-800">
      <KnowledgeDocumentOverview :document="document">
        <MarkdownRenderer
          :md="md"
        />
      </KnowledgeDocumentOverview>
    </div>
    <div class="mt-6 flex justify-end">
      <Button
        v-if="document?.is_ingested"
        severity="danger"
        :label="t('knowledge.documents.delete.button')"
        icon="pi pi-trash"
        :loading="isDeleting"
        @click="confirmDelete"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const { document, documentIsLoading } = useDocument()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const { deleteDocument, isPending: isDeleting } = useDeleteDocument()

const md = computed<string>(() => {
  if (documentIsLoading.value) {
    return ''
  }

  const content = document.value?.content
  if (!content) {
    return ''
  }

  return content
    // Replace our custom <figure>-tags surrounding our images
    .replace(/(?:<|&lt;)figure(?:>|&gt;)/g, '::MarkdownFigure\n')
    .replace(/(?:<|&lt;)\/figure(?:>|&gt;)/g, '\n::')

    // Replace our custom <table>-tag surrounding our tables
    .replace(/(?:<|&lt;)table(?:>|&gt;)/g, '::MarkdownTable\n')
    .replace(/(?:<|&lt;)\/table(?:>|&gt;)/g, '\n::')
})

const confirmDelete = () => {
  confirm.require({
    message: t('knowledge.documents.delete.confirm_message'),
    header: t('knowledge.documents.delete.confirm_title'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: t('knowledge.documents.delete.confirm_reject'),
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: t('knowledge.documents.delete.confirm_accept'),
      severity: 'danger',
    },
    accept: async () => {
      try {
        await deleteDocument({
          database: route.params.db as string,
          namespace: route.params.namespace as string,
          documentId: route.params.document_id as string,
        })
        toast.add({
          severity: 'success',
          summary: t('knowledge.documents.delete.success'),
          life: 3000,
        })
        router.push(localePath(`/service/knowledge/${route.params.db}/${route.params.namespace}`))
      }
      catch {
        toast.add({
          severity: 'error',
          summary: t('knowledge.documents.delete.error'),
          life: 5000,
        })
      }
    },
  })
}
</script>
