import { trace, SpanStatusCode } from '@opentelemetry/api'
import { ZoneContextManager } from '@opentelemetry/context-zone'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load'
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request'
import { resourceFromAttributes } from '@opentelemetry/resources'
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base'
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'

const SERVICE_NAME = 'attendflow-frontend'
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// Relative path: the Vite dev server forwards /otel to the OpenTelemetry Collector.
const OTLP_TRACES_PATH = '/otel/v1/traces'

const tracer = trace.getTracer(SERVICE_NAME)

export function recordBrowserError(error: unknown, context?: string): void {
  const span = tracer.startSpan('browser.error')
  if (context) span.setAttribute('error.context', context)
  span.recordException(error instanceof Error ? error : String(error))
  span.setStatus({ code: SpanStatusCode.ERROR })
  span.end()
}

export function initTelemetry(): void {
  if (import.meta.env.VITE_TELEMETRY_ENABLED === 'false') return

  const provider = new WebTracerProvider({
    resource: resourceFromAttributes({ 'service.name': SERVICE_NAME }),
    spanProcessors: [new BatchSpanProcessor(new OTLPTraceExporter({ url: OTLP_TRACES_PATH }))],
  })
  provider.register({ contextManager: new ZoneContextManager() })

  new DocumentLoadInstrumentation().enable()
  new XMLHttpRequestInstrumentation({
    // Send traceparent to the API so backend spans join the browser trace.
    // Limited to the API origin so trace IDs are not sent to third parties.
    propagateTraceHeaderCorsUrls: [new RegExp('^' + escapeRegExp(API_BASE_URL))],
    // The exporter's own requests would otherwise create spans about themselves.
    ignoreUrls: [/\/otel\//],
  }).enable()

  window.addEventListener('error', (event) => recordBrowserError(event.error ?? event.message, 'window.error'))
  window.addEventListener('unhandledrejection', (event) => recordBrowserError(event.reason, 'unhandledrejection'))
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
