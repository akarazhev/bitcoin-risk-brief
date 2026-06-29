import ReactEChartsCore from 'echarts-for-react/esm/core'
import type { EChartsReactProps } from 'echarts-for-react/lib/types'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, MarkLineComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  CanvasRenderer,
  GridComponent,
  LineChart,
  MarkLineComponent,
  TooltipComponent,
])

export default function Chart(props: EChartsReactProps) {
  return <ReactEChartsCore echarts={echarts} {...props} />
}
