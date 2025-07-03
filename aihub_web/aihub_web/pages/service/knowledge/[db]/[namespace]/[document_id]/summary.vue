<template>
  <StructuralColumn
    :title="t('knowledge.summary.title')"
    :close-route="`/service/knowledge/${route.params.db}/${route.params.namespace}`"
    :loading="summaryNodesAreLoading"
  >
    <div class="flex flex-col gap-16">
      <Tabs :value="1">
        <TabList>
          <Tab
            v-for="summary in summaryNodes"
            :key="summary.level"
            :value="summary.level"
          >
            {{ t('knowledge.summary.level') }} {{ summary.level }}
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel
            v-for="summary in summaryNodes"
            :key="summary.level"
            :value="summary.level"
          >
            <div v-if="summary.nodes.length > 0">
              <div
                v-for="(node, nodeIndex) in summary.nodes"
                :key="node.id"
              >
                <div
                  v-for="i in 6"
                  :key="i"
                >
                  <Component
                    :is="`h${i}`"
                    v-if="node[`h${i}`] && (nodeIndex === 0 || node[`h${i}`] !== summary.nodes[nodeIndex-1][`h${i}`])"
                    class="pl-2"
                  >
                    {{ node[`h${i}`] }}
                  </Component>
                </div>
                <KnowledgeNodeContent
                  :node="node"
                />
              </div>
            </div>
            <div v-else>
              {{ t("knowledge.summary.no_summaries_at_level") }}
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useSummaryNodes } from '@core/composables/document/useSummaryNodes'

const { t } = useI18n()
const route = useRoute()
const { summaryNodes, summaryNodesAreLoading } = useSummaryNodes()
</script>

<style scoped>
h1 {
  @apply mt-4 text-xl font-bold before:content-['#'] before:pr-1 before:text-gray-400;
}

h2 {
  @apply mt-4 text-lg font-bold before:content-['##'] before:pr-1 before:text-gray-400;
}

h3 {
  @apply mt-4 text-base font-bold before:content-['###'] before:pr-1 before:text-gray-400;;
}

h4 {
  @apply mt-3 font-bold before:content-['####'] before:pr-1 before:text-gray-400;;
}

h5 {
  @apply mt-2 font-bold before:content-['#####'] before:pr-1 before:text-gray-400;;
}

h6 {
  @apply mt-2 font-bold before:content-['######'] before:pr-1 before:text-gray-400;;
}
</style>
