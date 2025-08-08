<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('litellm.title')"
      :loading="pending"
      class="w-1/2 pr-2"
    >
      <div v-if="error" class="mb-4">
        <Message
          severity="error"
          :closable="false"
        >
          {{ t('litellm.error') }}: {{ error }}
        </Message>
      </div>

      <div v-if="!pending && !error && models">
        <DataTable
          :value="models"
          table-style="min-width: 50rem"
          :paginator="true"
          :rows="5"
          :rows-per-page-options="[5, 15, 25]"
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
          :current-page-report-template="t('litellm.table.pageReport')"
          responsive-layout="scroll"
        >
          <Column
            field="model_name"
            :header="t('litellm.table.modelName')"
            :sortable="true"
            style="min-width: 200px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <div class="flex items-center space-x-2">
                  <p class="font-medium text-sm text-gray-900 dark:text-gray-100">{{ data.model_name }}</p>
                  <Button
                    v-tooltip="t('litellm.table.copyModelName')"
                    icon="pi pi-copy"
                    severity="secondary"
                    text
                    size="small"
                    @click="copyToClipboard(data.model_name)"
                  />
                </div>
                <div class="md:hidden">
                  <p class="text-xs text-gray-600 dark:text-gray-400">{{ getProvider(data) }}</p>
                </div>
              </div>
            </template>
          </Column>

          <Column
            field="provider"
            :header="t('litellm.table.provider')"
            :sortable="true"
            class="hidden md:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <Tag
                :value="getProvider(data)"
                :severity="getProviderSeverity(getProvider(data))"
              />
            </template>
          </Column>

          <Column
            field="model_info.mode"
            :header="t('litellm.table.mode')"
            :sortable="true"
            class="hidden lg:table-cell"
            style="min-width: 150px"
          >
            <template #body="{ data }">
              <Tag
                :severity="getModeSeverity(data.model_info.mode)"
                :value="data.model_info.mode"
              />
            </template>
          </Column>

          <Column
            field="tokens"
            :header="t('litellm.table.tokens')"
            class="hidden lg:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <p class="text-xs text-gray-900 dark:text-gray-100">
                  {{ formatTokenLimits(data) }}
                </p>
              </div>
            </template>
          </Column>

          <Column
            field="cost"
            :header="t('litellm.table.costPer1M')"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <p class="text-xs font-medium text-gray-900 dark:text-gray-100">
                  {{ formatCostPer1M(data.model_info.input_cost_per_token) }}
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  {{ formatCostPer1M(data.model_info.output_cost_per_token) }}
                </p>
              </div>
            </template>
          </Column>

          <Column
            field="features"
            :header="t('litellm.table.features')"
            style="min-width: 200px"
          >
            <template #body="{ data }">
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="feature in getModelFeatures(data)"
                  :key="feature.name"
                  :value="feature.name"
                  :severity="feature.severity"
                  class="text-xs"
                />
                <span
                  v-if="!getModelFeatures(data).length"
                  class="text-xs text-gray-600 dark:text-gray-400"
                >
                  -
                </span>
              </div>
            </template>
          </Column>

          <Column
            field="rate_limits"
            :header="t('litellm.table.rateLimits')"
            class="hidden md:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="flex flex-col gap-1">
                <Badge
                  v-if="data.model_info.tpm"
                  :value="`${formatNumber(data.model_info.tpm)} TPM`"
                  severity="secondary"
                  class="text-xs"
                />
                <Badge
                  v-if="data.model_info.rpm"
                  :value="`${formatNumber(data.model_info.rpm)} RPM`"
                  severity="secondary"
                  class="text-xs"
                />
                <span
                  v-if="!data.model_info.tpm && !data.model_info.rpm"
                  class="text-xs text-gray-600 dark:text-gray-400"
                >
                  -
                </span>
              </div>
            </template>
          </Column>

          <Column
            field="details"
            :header="t('litellm.table.details')"
            style="min-width: 100px"
          >
            <template #body="{ data }">
              <Button
                icon="pi pi-info-circle"
                :label="t('litellm.table.detailsButton')"
                severity="info"
                outlined
                size="small"
                @click="showModelDetails(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>


      <Dialog
        v-model:visible="modelDialogVisible"
        modal
        :header="selectedModel?.model_name || ''"
        style="width: 1000px"
        :breakpoints="{ '960px': '90vw' }"
        class="model-details-dialog"
      >
        <div v-if="selectedModel" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.overview') }}</h3>
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelGroup') }}:</p>
                <p>{{ selectedModel.model_name }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.mode') }}:</p>
                <Tag
                  :severity="getModeSeverity(selectedModel.model_info.mode)"
                  :value="selectedModel.model_info.mode"
                />
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.provider') }}:</p>
                <div class="flex flex-wrap gap-1 mt-1">
                  <Tag
                    :value="getProvider(selectedModel)"
                    :severity="getProviderSeverity(getProvider(selectedModel))"
                  />
                </div>
              </div>
              <div v-if="selectedModel.model_info.id">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelId') }}:</p>
                <p class="text-xs font-mono break-all">{{ selectedModel.model_info.id }}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.tokenCost') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxInputTokens') }}:</p>
                <p>{{
                    selectedModel.model_info.max_input_tokens ? formatNumber(selectedModel.model_info.max_input_tokens) : t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxOutputTokens') }}:</p>
                <p>{{
                    selectedModel.model_info.max_output_tokens ? formatNumber(selectedModel.model_info.max_output_tokens) : t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.inputCostPer1M') }}:</p>
                <p>{{
                    selectedModel.model_info.input_cost_per_token ? formatCostPer1M(selectedModel.model_info.input_cost_per_token) : t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.outputCostPer1M') }}:</p>
                <p>{{
                    selectedModel.model_info.output_cost_per_token ? formatCostPer1M(selectedModel.model_info.output_cost_per_token) : t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div v-if="selectedModel.model_info.cache_read_input_token_cost">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.cacheReadCostPer1M') }}:</p>
                <p>{{ formatCostPer1M(selectedModel.model_info.cache_read_input_token_cost) }}</p>
              </div>
              <div v-if="selectedModel.model_info.output_vector_size">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.vectorSize') }}:</p>
                <p>{{ selectedModel.model_info.output_vector_size }}D</p>
              </div>
            </div>
          </div>

          <div v-if="selectedModel.model_info.tpm || selectedModel.model_info.rpm">
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.rateLimits') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="selectedModel.model_info.tpm">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.tokensPerMinute') }}:</p>
                <p>{{ formatNumber(selectedModel.model_info.tpm) }}</p>
              </div>
              <div v-if="selectedModel.model_info.rpm">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.requestsPerMinute') }}:</p>
                <p>{{ formatNumber(selectedModel.model_info.rpm) }}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.capabilities') }}</h3>
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="feature in getModelFeatures(selectedModel)"
                :key="feature.name"
                :value="feature.name"
                :severity="feature.severity"
                class="text-sm"
              />
              <p
                v-if="!getModelFeatures(selectedModel).length"
                class="text-gray-500"
              >
                {{ t('litellm.modelDetails.noCapabilities') }}
              </p>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.supportedParams') }}</h3>
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="param in selectedModel.model_info.supported_openai_params || []"
                :key="param"
                :value="param"
                severity="success"
                class="text-sm"
              />
              <p
                v-if="!selectedModel.model_info.supported_openai_params?.length"
                class="text-gray-500"
              >
                {{ t('litellm.modelDetails.notAvailable') }}
              </p>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.usageExample') }}</h3>
            <pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded text-sm overflow-x-auto"><code>{{
                getUsageExample(selectedModel)
              }}</code></pre>
          </div>
        </div>
      </Dialog>
    </StructuralColumn>

    <StructuralColumn :title="t('litellm.dashboard.title')" class="w-1/2 pl-2">
      <div class="w-full">
        <TabView class="w-full">
          <TabPanel :header="t('litellm.dashboard.globalUsage')">
            <div class="space-y-6">
              <div class="mb-4">
                <div class="mb-2">
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {{ t('litellm.dashboard.selectTimeRange') }}
                  </h3>
                </div>
                <div class="relative">
                  <div
                    @click="toggleDateRangeDropdown"
                    class="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 cursor-pointer hover:border-gray-400 dark:hover:border-gray-500 w-fit">
                    <i class="pi pi-clock text-gray-500 dark:text-gray-400"></i>
                    <span class="text-gray-700 dark:text-gray-300">{{ formatSelectedDateRange() }}</span>
                    <i class="pi pi-chevron-down text-gray-400 dark:text-gray-500 text-xs"></i>
                  </div>
                  
                  <div v-if="dateRangeDropdownVisible" class="absolute top-full left-0 z-[9999] min-w-[600px] mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl">
                    <div class="flex">
                      <!-- Relative Time Section -->
                      <div class="w-1/2 border-r border-gray-200 dark:border-gray-700">
                        <div class="p-3 border-b border-gray-200 dark:border-gray-700">
                          <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ t('litellm.dashboard.relativeTime') }}</span>
                        </div>
                        <div class="h-[350px] overflow-y-auto">
                          <div 
                            v-for="option in relativeDateOptions" 
                            :key="option.value"
                            @click="selectRelativeDate(option)"
                            class="flex items-center justify-between px-5 py-4 cursor-pointer border-b border-gray-100 dark:border-gray-700 transition-colors hover:bg-gray-50 dark:hover:bg-gray-700"
                            :class="{
                              'bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 border-blue-200 dark:border-blue-700': selectedDateRange.type === 'relative' && selectedDateRange.value === option.value
                            }"
                          >
                            <span 
                              class="text-sm"
                              :class="{
                                'text-blue-700 dark:text-blue-300 font-medium': selectedDateRange.type === 'relative' && selectedDateRange.value === option.value,
                                'text-gray-700 dark:text-gray-300': !(selectedDateRange.type === 'relative' && selectedDateRange.value === option.value)
                              }"
                            >
                              {{ option.label }}
                            </span>
                            <span 
                              class="text-xs px-2 py-1 rounded"
                              :class="{
                                'text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-800': selectedDateRange.type === 'relative' && selectedDateRange.value === option.value,
                                'text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700': !(selectedDateRange.type === 'relative' && selectedDateRange.value === option.value)
                              }"
                            >
                              {{ option.shortLabel }}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <!-- Custom Date Section -->
                      <div class="w-1/2 relative">
                        <div class="p-3.5 border-b border-gray-200 dark:border-gray-700">
                          <div class="flex items-center gap-2">
                            <i class="pi pi-calendar text-gray-600 dark:text-gray-400"></i>
                            <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ t('litellm.dashboard.customDateRange') }}</span>
                          </div>
                        </div>
                        <div class="p-6 space-y-6 pb-20">
                          <div>
                            <label class="text-sm text-gray-700 dark:text-gray-300 mb-1 block">{{ t('litellm.dashboard.startDate') }}</label>
                            <input 
                              v-model="customDateRange.startDate"
                              class="w-65 px-3 py-2 text-sm border rounded-md cursor-pointer hover:border-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" 
                              type="date"
                            />
                          </div>
                          <div>
                            <label class="text-sm text-gray-700 dark:text-gray-300 mb-1 block">{{ t('litellm.dashboard.endDate') }}</label>
                            <input 
                              v-model="customDateRange.endDate"
                              class="w-65 px-3 py-2 text-sm border rounded-md cursor-pointer hover:border-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" 
                              type="date"
                            />
                          </div>
                          <div class="bg-blue-50 dark:bg-blue-900/30 p-3 rounded-md">
                            <div class="text-xs text-blue-700 dark:text-blue-300 font-medium">{{ t('litellm.dashboard.preview') }}:</div>
                            <div class="text-sm text-blue-800 dark:text-blue-200">{{ formatCustomDatePreview() }}</div>
                          </div>
                        </div>
                        <div class="absolute bottom-4 right-4">
                          <div class="flex gap-2">
                            <button 
                              @click="cancelDateSelection"
                              class="px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 bg-transparent border border-blue-600 dark:border-blue-400 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/20"
                            >
                              {{ t('litellm.dashboard.cancel') }}
                            </button>
                            <button 
                              @click="applyCustomDateRange"
                              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-blue-500 border border-blue-600 dark:border-blue-500 rounded-md hover:bg-blue-700 dark:hover:bg-blue-600"
                            >
                              {{ t('litellm.dashboard.apply') }}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <TabView class="w-full">
                <TabPanel :header="t('litellm.dashboard.cost')">
                  <div class="space-y-6">
                    <div class="grid grid-cols-5 gap-4">
                      <div
                        class="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 p-4 rounded-lg border border-blue-200 dark:border-blue-700">
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm text-blue-600 dark:text-blue-400 font-medium">
                              {{ t('litellm.dashboard.totalSpend') }}</p>
                            <p class="text-2xl font-bold text-blue-900 dark:text-blue-100">
                              ${{ getTotalSpend().toFixed(4) }}</p>
                          </div>
                          <i class="pi pi-dollar text-blue-500 dark:text-blue-400 text-2xl"></i>
                        </div>
                      </div>

                      <div
                        class="bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 p-4 rounded-lg border border-green-200 dark:border-green-700">
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm text-green-600 dark:text-green-400 font-medium">
                              {{ t('litellm.dashboard.totalRequests') }}</p>
                            <p class="text-2xl font-bold text-green-900 dark:text-green-100">
                              {{ formatNumber(getTotalRequests()) }}</p>
                          </div>
                          <i class="pi pi-send text-green-500 dark:text-green-400 text-2xl"></i>
                        </div>
                      </div>

                      <div
                        class="bg-gradient-to-r from-emerald-50 to-emerald-100 dark:from-emerald-900/30 dark:to-emerald-800/30 p-4 rounded-lg border border-emerald-200 dark:border-emerald-700">
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                              {{ t('litellm.dashboard.successfulRequests') }}</p>
                            <p class="text-2xl font-bold text-emerald-900 dark:text-emerald-100">
                              {{ formatNumber(getTotalSuccessfulRequests()) }}</p>
                          </div>
                          <i class="pi pi-check-circle text-emerald-500 dark:text-emerald-400 text-2xl"></i>
                        </div>
                      </div>

                      <div
                        class="bg-gradient-to-r from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 p-4 rounded-lg border border-red-200 dark:border-red-700">
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm text-red-600 dark:text-red-400 font-medium">
                              {{ t('litellm.dashboard.failedRequests') }}</p>
                            <p class="text-2xl font-bold text-red-900 dark:text-red-100">
                              {{ formatNumber(getTotalFailedRequests()) }}</p>
                          </div>
                          <i class="pi pi-times-circle text-red-500 dark:text-red-400 text-2xl"></i>
                        </div>
                      </div>

                      <div
                        class="bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 p-4 rounded-lg border border-purple-200 dark:border-purple-700">
                        <div class="flex items-center justify-between">
                          <div>
                            <p class="text-sm text-purple-600 dark:text-purple-400 font-medium">
                              {{ t('litellm.dashboard.totalTokens') }}</p>
                            <p class="text-2xl font-bold text-purple-900 dark:text-purple-100">
                              {{ formatNumber(getTotalTokens()) }}</p>
                          </div>
                          <i class="pi pi-code text-purple-500 dark:text-purple-400 text-2xl"></i>
                        </div>
                      </div>
                    </div>

                    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          {{ t('litellm.dashboard.dailySpend') }}</h3>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Last 7 days</div>
                      </div>
                      <div
                        class="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-700 rounded border-2 border-dashed border-gray-300 dark:border-gray-600">
                        <div class="text-center">
                          <i class="pi pi-chart-line text-gray-400 dark:text-gray-500 text-4xl mb-2"></i>
                          <p class="text-gray-500 dark:text-gray-400">{{ t('litellm.dashboard.chartPlaceholder') }}</p>
                        </div>
                      </div>
                    </div>

                    <div class="grid grid-cols-2 gap-6">
                      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {{ t('litellm.dashboard.topApiKeys') }}</h3>
                          <Button
                            :label="t('litellm.dashboard.tableView')"
                            icon="pi pi-table"
                            text
                            size="small"
                            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                          />
                        </div>
                        <DataTable :value="getTopApiKeys()" size="small" class="border-0">
                          <Column field="keyId" :header="t('litellm.dashboard.keyId')" class="text-xs"></Column>
                          <Column field="keyAlias" :header="t('litellm.dashboard.keyAlias')" class="text-xs"></Column>
                          <Column field="spend" :header="t('litellm.dashboard.spend')" class="text-xs"></Column>
                        </DataTable>
                      </div>

                      <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-4">
                          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {{ t('litellm.dashboard.topModels') }}</h3>
                          <div class="flex items-center gap-2">
                            <Button
                              label="Public Model Name"
                              text
                              size="small"
                              class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 px-2 py-1 text-xs"
                            />
                            <span class="text-gray-300 dark:text-gray-600">|</span>
                            <Button
                              label="LiteLLM Model Name"
                              text
                              size="small"
                              class="text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 px-2 py-1 text-xs"
                            />
                          </div>
                        </div>
                        <DataTable :value="getTopModels()" size="small" class="border-0" scrollable
                                   scrollHeight="200px">
                          <Column field="model" :header="t('litellm.dashboard.model')" class="text-xs"
                                  style="min-width: 120px"></Column>
                          <Column field="spend" :header="t('litellm.dashboard.spend')" class="text-xs"
                                  style="min-width: 80px"></Column>
                          <Column field="successful" :header="t('litellm.dashboard.successful')"
                                  class="text-xs text-green-600 dark:text-green-400" style="min-width: 60px"></Column>
                          <Column field="failed" :header="t('litellm.dashboard.failed')"
                                  class="text-xs text-red-600 dark:text-red-400" style="min-width: 50px"></Column>
                        </DataTable>
                      </div>
                    </div>

                    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          {{ t('litellm.dashboard.spendByProvider') }}</h3>
                        <div class="text-sm text-gray-600 dark:text-gray-400">Total: ${{
                            getTotalSpend().toFixed(4)
                          }}
                        </div>
                      </div>
                      <div class="grid grid-cols-2 gap-6">
                        <div
                          class="h-48 flex items-center justify-center bg-gray-50 dark:bg-gray-700 rounded border-2 border-dashed border-gray-300 dark:border-gray-600">
                          <div class="text-center">
                            <i class="pi pi-chart-pie text-gray-400 dark:text-gray-500 text-3xl mb-2"></i>
                            <p class="text-gray-500 dark:text-gray-400 text-sm">
                              {{ t('litellm.dashboard.pieChartPlaceholder') }}</p>
                          </div>
                        </div>
                        <div>
                          <DataTable :value="getProviderBreakdown()" size="small" class="border-0">
                            <Column field="provider" :header="t('litellm.dashboard.provider')" class="text-xs">
                              <template #body="{ data }">
                                <div class="flex items-center gap-2">
                                  <div :class="`w-3 h-3 rounded ${data.color}`"></div>
                                  <span class="text-gray-900 dark:text-gray-100">{{ data.provider }}</span>
                                </div>
                              </template>
                            </Column>
                            <Column field="spend" :header="t('litellm.dashboard.spend')" class="text-xs"></Column>
                            <Column field="percentage" :header="t('litellm.dashboard.percentage')"
                                    class="text-xs"></Column>
                          </DataTable>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabPanel>

                <TabPanel :header="t('litellm.dashboard.modelActivity')">
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                      {{ t('litellm.dashboard.modelActivity') }}</h3>
                    <DataTable :value="getTopModels()" size="small" :paginator="true" :rows="10" class="border-0">
                      <Column field="model" :header="t('litellm.dashboard.model')" :sortable="true"
                              class="text-xs"></Column>
                      <Column field="spend" :header="t('litellm.dashboard.spend')" :sortable="true"
                              class="text-xs"></Column>
                      <Column field="successful" :header="t('litellm.dashboard.successful')" :sortable="true"
                              class="text-xs text-green-600 dark:text-green-400"></Column>
                      <Column field="failed" :header="t('litellm.dashboard.failed')" :sortable="true"
                              class="text-xs text-red-600 dark:text-red-400"></Column>
                      <Column field="tokens" :header="t('litellm.dashboard.tokens')" :sortable="true"
                              class="text-xs"></Column>
                    </DataTable>
                  </div>
                </TabPanel>

                <TabPanel :header="t('litellm.dashboard.keyActivity')">
                  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                      {{ t('litellm.dashboard.keyActivity') }}</h3>
                    <DataTable :value="getTopApiKeys()" size="small" :paginator="true" :rows="10" class="border-0">
                      <Column field="keyId" :header="t('litellm.dashboard.keyId')" :sortable="true"
                              class="text-xs"></Column>
                      <Column field="keyAlias" :header="t('litellm.dashboard.keyAlias')" :sortable="true"
                              class="text-xs"></Column>
                      <Column field="spend" :header="t('litellm.dashboard.spend')" :sortable="true"
                              class="text-xs"></Column>
                    </DataTable>
                  </div>
                </TabPanel>
              </TabView>
            </div>
          </TabPanel>

          <TabPanel :header="t('litellm.dashboard.teamUsage')">
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="text-center py-8">
                <i class="pi pi-users text-gray-400 dark:text-gray-500 text-4xl mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">
                  {{ t('litellm.dashboard.teamUsage') }}</h3>
                <p class="text-gray-500 dark:text-gray-400">{{ t('litellm.dashboard.noTeamData') }}</p>
              </div>
            </div>
          </TabPanel>

          <TabPanel :header="t('litellm.dashboard.tagUsage')">
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="text-center py-8">
                <i class="pi pi-tags text-gray-400 dark:text-gray-500 text-4xl mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">
                  {{ t('litellm.dashboard.tagUsage') }}</h3>
                <p class="text-gray-500 dark:text-gray-400">{{ t('litellm.dashboard.noTagData') }}</p>
              </div>
            </div>
          </TabPanel>

          <TabPanel :header="t('litellm.dashboard.userAgentActivity')">
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div class="text-center py-8">
                <i class="pi pi-desktop text-gray-400 dark:text-gray-500 text-4xl mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">
                  {{ t('litellm.dashboard.userAgentActivity') }}</h3>
                <p class="text-gray-500 dark:text-gray-400">{{ t('litellm.dashboard.noUserAgentData') }}</p>
              </div>
            </div>
          </TabPanel>
        </TabView>
      </div>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
interface CustomTokenizer {
  identifier: string
  revision: string
  auth_token?: string
}

interface LiteLLMParams {
  api_base?: string
  api_version?: string
  use_in_pass_through?: boolean
  use_litellm_proxy?: boolean
  merge_reasoning_content_in_choices?: boolean
  model: string
}

interface ModelInfo {
  id?: string
  db_model?: boolean
  base_model?: string
  mode: string
  key: string
  max_tokens?: number
  max_input_tokens?: number
  max_output_tokens?: number
  input_cost_per_token?: number
  output_cost_per_token?: number
  cache_creation_input_token_cost?: number
  cache_read_input_token_cost?: number
  input_cost_per_character?: number
  input_cost_per_token_above_128k_tokens?: number
  input_cost_per_token_above_200k_tokens?: number
  input_cost_per_query?: number
  input_cost_per_second?: number
  input_cost_per_audio_token?: number
  input_cost_per_token_batches?: number
  output_cost_per_token_batches?: number
  output_cost_per_audio_token?: number
  output_cost_per_character?: number
  output_cost_per_reasoning_token?: number
  output_cost_per_token_above_128k_tokens?: number
  output_cost_per_character_above_128k_tokens?: number
  output_cost_per_token_above_200k_tokens?: number
  output_cost_per_second?: number
  output_cost_per_image?: number
  citation_cost_per_token?: number
  search_context_cost_per_query?: number
  output_vector_size?: number
  litellm_provider?: string
  custom_tokenizer?: CustomTokenizer
  supports_system_messages?: boolean
  supports_response_schema?: boolean
  supports_vision?: boolean
  supports_function_calling?: boolean
  supports_tool_choice?: boolean
  supports_assistant_prefill?: boolean
  supports_prompt_caching?: boolean
  supports_audio_input?: boolean
  supports_audio_output?: boolean
  supports_pdf_input?: boolean
  supports_embedding_image_input?: boolean
  supports_native_streaming?: boolean
  supports_web_search?: boolean
  supports_url_context?: boolean
  supports_reasoning?: boolean
  supports_computer_use?: boolean
  tpm?: number
  rpm?: number
  supported_openai_params?: string[]
}

interface LLMModel {
  model_name: string
  litellm_params: LiteLLMParams
  model_info: ModelInfo
}

definePageMeta({
  layout: 'default',
})

const {t} = useI18n()
const toast = useToast()

const {data: models, pending, error} = await useFetch<LLMModel[]>('/api/v1/litellm/model_info')

const modelDialogVisible = ref(false)
const selectedModel = ref<LLMModel | null>(null)

// Date range dropdown functionality
const dateRangeDropdownVisible = ref(false)

interface RelativeDateOption {
  label: string
  shortLabel: string
  value: string
  days: number
}

interface DateRange {
  type: 'relative' | 'custom'
  value?: string
  startDate?: string
  endDate?: string
}

const selectedDateRange = ref<DateRange>({
  type: 'relative',
  value: '7d'
})

const customDateRange = ref({
  startDate: '2025-08-01',
  endDate: '2025-08-08'
})

const relativeDateOptions: RelativeDateOption[] = [
  { label: 'Today', shortLabel: 'today', value: 'today', days: 0 },
  { label: 'Last 7 days', shortLabel: '7d', value: '7d', days: 7 },
  { label: 'Last 30 days', shortLabel: '30d', value: '30d', days: 30 },
  { label: 'Month to date', shortLabel: 'MTD', value: 'mtd', days: 30 },
  { label: 'Year to date', shortLabel: 'YTD', value: 'ytd', days: 365 }
]

// Usage data fetching
interface DailyActivityResponse {
  results: Array<{
    date: string
    metrics: {
      spend: number
      prompt_tokens: number
      completion_tokens: number
      cache_read_input_tokens: number
      cache_creation_input_tokens: number
      total_tokens: number
      successful_requests: number
      failed_requests: number
      api_requests: number
    }
    breakdown: {
      models: Record<string, {
        metrics: {
          spend: number
          prompt_tokens: number
          completion_tokens: number
          cache_read_input_tokens: number
          cache_creation_input_tokens: number
          total_tokens: number
          successful_requests: number
          failed_requests: number
          api_requests: number
        }
      }>
    }
  }>
}

// Reactive date range parameters
const dateRangeParams = computed(() => {
  if (selectedDateRange.value.type === 'custom') {
    return {
      start_date: selectedDateRange.value.startDate || '2025-08-01',
      end_date: selectedDateRange.value.endDate || '2025-08-08',
      page_size: 1000,
      page: 1
    }
  } else {
    const { startDate, endDate } = getRelativeDateRange(selectedDateRange.value.value || '7d')
    return {
      start_date: startDate,
      end_date: endDate,
      page_size: 1000,
      page: 1
    }
  }
})

const {data: usageData, refresh: refreshUsageData} = await useFetch<DailyActivityResponse>('/api/v1/litellm/daily_activity', {
  query: dateRangeParams
})

function getProvider(model: LLMModel): string {
  if (model.model_info.litellm_provider) {
    return model.model_info.litellm_provider
  }

  const modelName = model.model_name
  if (modelName.includes('azure/')) return 'azure'
  if (modelName.includes('google/') || modelName.includes('gemini')) return 'google'
  if (modelName.includes('openai/')) return 'openai'
  if (modelName.includes('anthropic/')) return 'anthropic'
  if (modelName.includes('local/')) return 'local'
  if (modelName.includes('text-embedding')) return 'openai'
  return 'unknown'
}

function getProviderSeverity(provider: string): string {
  switch (provider) {
    case 'azure':
      return 'info'
    case 'google':
      return 'success'
    case 'openai':
      return 'warn'
    case 'anthropic':
      return 'danger'
    case 'local':
      return 'secondary'
    default:
      return 'secondary'
  }
}

function getModeSeverity(mode: string): string {
  switch (mode) {
    case 'chat':
      return 'info'
    case 'embedding':
      return 'success'
    case 'image_generation':
      return 'warn'
    case 'audio_transcription':
    case 'audio_speech':
      return 'help'
    default:
      return 'secondary'
  }
}

function formatTokenLimits(model: LLMModel): string {
  const input = model.model_info.max_input_tokens
  const output = model.model_info.max_output_tokens

  if (input && output) {
    return `${formatNumber(input)} / ${formatNumber(output)}`
  } else if (input) {
    return `${formatNumber(input)} / -`
  } else if (output) {
    return `- / ${formatNumber(output)}`
  }
  return '- / -'
}

function formatCostPer1M(costPerToken?: number): string {
  if (!costPerToken) return '-'
  const costPer1M = costPerToken * 1000000
  return `$${costPer1M.toFixed(2)}`
}

function getModelFeatures(model: LLMModel): Array<{ name: string, severity: string }> {
  const features: Array<{ name: string, severity: string }> = []

  if (model.model_info.supports_vision) {
    features.push({name: 'Vision', severity: 'success'})
  }

  if (model.model_info.supports_function_calling) {
    features.push({name: 'Function Calling', severity: 'info'})
  }

  if (model.model_info.supports_web_search) {
    features.push({name: 'Web Search', severity: 'help'})
  }

  if (model.model_info.supports_reasoning) {
    features.push({name: 'Reasoning', severity: 'warn'})
  }

  if (model.model_info.supports_prompt_caching) {
    features.push({name: 'Caching', severity: 'secondary'})
  }

  if (model.model_info.supports_audio_input) {
    features.push({name: 'Audio Input', severity: 'info'})
  }

  if (model.model_info.supports_audio_output) {
    features.push({name: 'Audio Output', severity: 'info'})
  }

  if (model.model_info.supports_pdf_input) {
    features.push({name: 'PDF Input', severity: 'success'})
  }

  if (model.model_info.supports_computer_use) {
    features.push({name: 'Computer Use', severity: 'danger'})
  }

  if (model.model_info.output_vector_size) {
    features.push({name: `${model.model_info.output_vector_size}D`, severity: 'secondary'})
  }

  return features
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.add({
      severity: 'success',
      summary: t('litellm.copied'),
      detail: t('litellm.copiedDetail', {text}),
      life: 3000
    })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: t('litellm.copyFailed'),
      detail: t('litellm.copyFailedDetail'),
      life: 3000
    })
  }
}

function getUsageExample(model: LLMModel): string {
  const isImageGeneration = model.model_info.mode === 'image_generation'
  const isEmbedding = model.model_info.mode === 'embedding'

  if (isImageGeneration) {
    return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.images.generate(
    model="${model.model_name}",
    prompt="A beautiful sunset over mountains",
    size="1024x1024",
    n=1
)

print(response.data[0].url)`
  }

  if (isEmbedding) {
    return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.embeddings.create(
    model="${model.model_name}",
    input="Your text to embed here"
)

print(response.data[0].embedding)`
  }

  return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.chat.completions.create(
    model="${model.model_name}",
    messages=[
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ]
)

print(response.choices[0].message.content)`
}

function getModelSpend(modelName: string): number {
  if (!usageData.value?.results?.length) return 0

  for (const result of usageData.value.results) {
    if (result.breakdown.models[modelName]) {
      return result.breakdown.models[modelName].metrics.spend
    }
  }
  return 0
}

function getModelRequests(modelName: string): number {
  if (!usageData.value?.results?.length) return 0

  for (const result of usageData.value.results) {
    if (result.breakdown.models[modelName]) {
      return result.breakdown.models[modelName].metrics.api_requests
    }
  }
  return 0
}

function getModelSuccessfulRequests(modelName: string): number {
  if (!usageData.value?.results?.length) return 0

  for (const result of usageData.value.results) {
    if (result.breakdown.models[modelName]) {
      return result.breakdown.models[modelName].metrics.successful_requests
    }
  }
  return 0
}

function getModelTokens(modelName: string): number {
  if (!usageData.value?.results?.length) return 0

  for (const result of usageData.value.results) {
    if (result.breakdown.models[modelName]) {
      return result.breakdown.models[modelName].metrics.total_tokens
    }
  }
  return 0
}

function getTotalSpend(): number {
  if (!usageData.value?.results?.length) return 0
  return usageData.value.results.reduce((total, result) => total + result.metrics.spend, 0)
}

function getTotalRequests(): number {
  if (!usageData.value?.results?.length) return 0
  return usageData.value.results.reduce((total, result) => total + result.metrics.api_requests, 0)
}

function getTotalSuccessfulRequests(): number {
  if (!usageData.value?.results?.length) return 0
  return usageData.value.results.reduce((total, result) => total + result.metrics.successful_requests, 0)
}

function getTotalFailedRequests(): number {
  if (!usageData.value?.results?.length) return 0
  return usageData.value.results.reduce((total, result) => total + result.metrics.failed_requests, 0)
}

function getTotalTokens(): number {
  if (!usageData.value?.results?.length) return 0
  return usageData.value.results.reduce((total, result) => total + result.metrics.total_tokens, 0)
}

function getAverageCostPerRequest(): number {
  const totalSpend = getTotalSpend()
  const totalRequests = getTotalRequests()
  if (totalRequests === 0) return 0
  return totalSpend / totalRequests
}

function getTopApiKeys() {
  return [
    {keyId: '826f0e5...', keyAlias: 'test', spend: '$0.00'},
    {keyId: '-', keyAlias: '-', spend: '$0.00'}
  ]
}

function getTopModels() {
  if (!usageData.value?.results?.length) return []

  const modelMetrics = []
  for (const result of usageData.value.results) {
    for (const [modelName, modelData] of Object.entries(result.breakdown.models)) {
      modelMetrics.push({
        model: modelName,
        spend: `$${modelData.metrics.spend.toFixed(4)}`,
        successful: modelData.metrics.successful_requests,
        failed: modelData.metrics.failed_requests,
        tokens: formatNumber(modelData.metrics.total_tokens)
      })
    }
  }

  return modelMetrics.sort((a, b) => parseFloat(b.spend.replace('$', '')) - parseFloat(a.spend.replace('$', '')))
}

function getProviderBreakdown() {
  if (!usageData.value?.results?.length) return []

  const totalSpend = getTotalSpend()
  const providers = new Map()

  for (const result of usageData.value.results) {
    for (const [modelName, modelData] of Object.entries(result.breakdown.models)) {
      const provider = models.value?.find(m => m.model_name === modelName)?.model_info.litellm_provider || 'unknown'
      const currentSpend = providers.get(provider) || 0
      providers.set(provider, currentSpend + modelData.metrics.spend)
    }
  }

  const colors = {
    azure: 'bg-blue-500',
    openai: 'bg-green-500',
    google: 'bg-yellow-500',
    gemini: 'bg-purple-500',
    local: 'bg-gray-500',
    unknown: 'bg-red-500'
  }

  return Array.from(providers.entries()).map(([provider, spend]) => ({
    provider,
    spend: `$${spend.toFixed(4)}`,
    percentage: totalSpend > 0 ? `${((spend / totalSpend) * 100).toFixed(1)}%` : '0%',
    color: colors[provider] || colors.unknown
  })).sort((a, b) => parseFloat(b.spend.replace('$', '')) - parseFloat(a.spend.replace('$', '')))
}

// Date range utility functions
function getRelativeDateRange(value: string): { startDate: string, endDate: string } {
  const today = new Date()
  const endDate = today.toISOString().split('T')[0]
  
  let startDate: string
  
  switch (value) {
    case 'today':
      startDate = endDate
      break
    case '7d':
      const sevenDaysAgo = new Date(today)
      sevenDaysAgo.setDate(today.getDate() - 7)
      startDate = sevenDaysAgo.toISOString().split('T')[0]
      break
    case '30d':
      const thirtyDaysAgo = new Date(today)
      thirtyDaysAgo.setDate(today.getDate() - 30)
      startDate = thirtyDaysAgo.toISOString().split('T')[0]
      break
    case 'mtd':
      startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
      break
    case 'ytd':
      startDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0]
      break
    default:
      const defaultSevenDaysAgo = new Date(today)
      defaultSevenDaysAgo.setDate(today.getDate() - 7)
      startDate = defaultSevenDaysAgo.toISOString().split('T')[0]
  }
  
  return { startDate, endDate }
}

// Dropdown handler functions
function toggleDateRangeDropdown() {
  dateRangeDropdownVisible.value = !dateRangeDropdownVisible.value
}

function selectRelativeDate(option: RelativeDateOption) {
  selectedDateRange.value = {
    type: 'relative',
    value: option.value
  }
  dateRangeDropdownVisible.value = false
  refreshUsageData()
}

function applyCustomDateRange() {
  selectedDateRange.value = {
    type: 'custom',
    startDate: customDateRange.value.startDate,
    endDate: customDateRange.value.endDate
  }
  dateRangeDropdownVisible.value = false
  refreshUsageData()
}

function cancelDateSelection() {
  // Reset custom date range to match current selection if it was custom
  if (selectedDateRange.value.type === 'custom') {
    customDateRange.value = {
      startDate: selectedDateRange.value.startDate || '2025-08-01',
      endDate: selectedDateRange.value.endDate || '2025-08-08'
    }
  }
  dateRangeDropdownVisible.value = false
}

function formatSelectedDateRange(): string {
  if (selectedDateRange.value.type === 'relative') {
    const option = relativeDateOptions.find(opt => opt.value === selectedDateRange.value.value)
    return option ? option.label : 'Last 7 days'
  } else {
    const startDate = selectedDateRange.value.startDate
    const endDate = selectedDateRange.value.endDate
    if (startDate && endDate) {
      const start = new Date(startDate)
      const end = new Date(endDate)
      return `${start.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })} - ${end.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })}`
    }
    return '1 Aug - 8 Aug'
  }
}

function formatCustomDatePreview(): string {
  const startDate = customDateRange.value.startDate
  const endDate = customDateRange.value.endDate
  if (startDate && endDate) {
    const start = new Date(startDate)
    const end = new Date(endDate)
    return `${start.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })}, 00:00 - ${end.toLocaleDateString('en-US', { day: 'numeric', month: 'short' })}, 23:59`
  }
  return 'Invalid date range'
}

// Close dropdown when clicking outside
onMounted(() => {
  document.addEventListener('click', (event) => {
    const dropdown = document.querySelector('.date-range-dropdown')
    if (dropdown && !dropdown.contains(event.target as Node)) {
      dateRangeDropdownVisible.value = false
    }
  })
})

function showModelDetails(model: LLMModel) {
  selectedModel.value = model
  modelDialogVisible.value = true
}
</script>
