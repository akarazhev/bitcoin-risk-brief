import type { Locale } from './locales'

export interface MethodologySection {
  heading: string
  body: string[]
}

export interface MethodologyCopy {
  title: string
  intro: string
  translationNotice: string | null
  sections: MethodologySection[]
  referenceLinkLabel: string
}

export const BAND_LOW = 0.3
export const BAND_HIGH = 0.7
export const METHODOLOGY_VERSION = 'crypto-scout-canonical-v1.1'

export const methodologyCopy: Record<Locale, MethodologyCopy> = {
  en: {
    title: 'How to read Bitcoin Risk Brief',
    intro: 'An interpretation guide to the daily risk number, how it is classified, and where its limits begin.',
    translationNotice: null,
    sections: [
      {
        heading: 'What this number is.',
        body: [
          'A single value from 0.0 to 1.0 describing how stretched the Bitcoin market looks against its own history, recomputed once a day from completed daily data. It is not a probability that the price will fall, not a target, and not an instruction to buy or sell anything. It compresses three observations into one number, and like every compression it discards more than it keeps.',
        ],
      },
      {
        heading: 'Why today reads low, neutral, or high.',
        body: [
          'Below 0.30 is low. From 0.30 up to but not including 0.70 is neutral. 0.70 and above is high. The boundaries are fixed, so the state changes only when the value crosses one. A reading of 0.25 is low because it sits below 0.30, and it becomes neutral at 0.30 — not at the moment the market feels different.',
        ],
      },
      {
        heading: 'What goes into it.',
        body: [
          'Three inputs: how far the price sits from its long-run trend, how violently it has moved recently, and how much trading activity there is relative to the size of the market. Each is compared against its own history rather than an absolute level, which is why a price that would have been extreme in 2015 need not be extreme now. The exact formulas, weights and windows are published in the technical reference.',
        ],
      },
      {
        heading: 'The price shown here is not a quote.',
        body: [
          'It is the HLC3 average of the last completed daily candle — high, low and close divided by three. It is a model input, not the current market price, and it will differ from what an exchange shows right now. Nothing on this page updates intraday.',
        ],
      },
      {
        heading: 'The level ladder is not a forecast.',
        body: [
          'It answers a backwards question: holding everything except price fixed, at what price would the model report each risk level? That is a description of the model\'s shape, not a prediction, a target, a support line, or a trade. If the other inputs move, the ladder moves with them.',
        ],
      },
      {
        heading: "When not to trust today's number.",
        body: [
          'The data has to be current and it has to have passed validation. A separate readiness check reports both, and it answers with HTTP 503 instead of a green light when either fails. The data endpoints behave differently on purpose: they keep returning the last rows they hold, so a value means nothing without the covered date beside it and a readiness state that agrees. This page shows both, and says plainly when the data has fallen behind.',
        ],
      },
      {
        heading: 'What the model cannot see.',
        body: [
          'It has no on-chain data, no news, no order-book depth, and no knowledge of anything that happened after the last completed day. It works on daily bars, so a fall and recovery inside one day is invisible to it. It assumes the future resembles the past well enough for a historical comparison to mean something, and that assumption fails exactly when it would be most useful.',
        ],
      },
      {
        heading: 'What happens when the methodology changes.',
        body: [
          'The methodology carries a version, currently crypto-scout-canonical-v1.1, reported by the readiness check and alongside the level ladder. A change that alters the numbers gets a new version string, so a value recorded earlier can always be traced back to the rules that produced it.',
        ],
      },
    ],
    referenceLinkLabel: 'Read the technical methodology',
  },
  ru: {
    title: 'Как читать Bitcoin Risk Brief',
    intro: 'Руководство по интерпретации ежедневного показателя риска, его классификации и ограничениям.',
    translationNotice: 'Эта страница является переводом; английская версия имеет преимущественную силу.',
    sections: [
      {
        heading: 'Что представляет собой это число.',
        body: [
          'Это одно значение от 0.0 до 1.0, которое показывает, насколько растянутым выглядит рынок биткоина относительно собственной истории, и пересчитывается раз в день по завершённым дневным данным. Это не вероятность падения цены, не целевой уровень и не указание что-либо покупать или продавать. Показатель объединяет три наблюдения в одно число и, как любое сжатие, отбрасывает больше информации, чем сохраняет.',
        ],
      },
      {
        heading: 'Почему сегодня уровень низкий, нейтральный или высокий.',
        body: [
          'Ниже 0.30 — низкий уровень. От 0.30 до 0.70, не включая 0.70, — нейтральный. 0.70 и выше — высокий. Границы фиксированы, поэтому состояние меняется только при пересечении одной из них. Значение 0.25 считается низким, потому что оно ниже 0.30, и становится нейтральным при 0.30, а не тогда, когда рынок начинает ощущаться иначе.',
        ],
      },
      {
        heading: 'Что входит в показатель.',
        body: [
          'Три входных фактора: насколько цена отклонена от долгосрочного тренда, насколько резко она двигалась в последнее время и какова торговая активность относительно размера рынка. Каждый фактор сравнивается с собственной историей, а не с абсолютным уровнем, поэтому цена, которая была бы экстремальной в 2015 году, не обязательно является экстремальной сейчас. Точные формулы, веса и окна опубликованы в техническом описании.',
        ],
      },
      {
        heading: 'Показанная здесь цена не является котировкой.',
        body: [
          'Это среднее HLC3 последней завершённой дневной свечи: максимум, минимум и цена закрытия, делённые на три. Это вход модели, а не текущая рыночная цена, поэтому он будет отличаться от того, что биржа показывает прямо сейчас. Ничто на этой странице не обновляется внутри дня.',
        ],
      },
      {
        heading: 'Лестница уровней не является прогнозом.',
        body: [
          'Она отвечает на обратный вопрос: если зафиксировать всё, кроме цены, при какой цене модель покажет каждый уровень риска? Это описание формы модели, а не прогноз, цель, уровень поддержки или сделка. Если меняются другие входные данные, лестница движется вместе с ними.',
        ],
      },
      {
        heading: 'Когда не следует доверять сегодняшнему числу.',
        body: [
          'Данные должны быть актуальными и пройти проверку. Отдельная проверка готовности сообщает оба состояния и отвечает HTTP 503 вместо сигнала готовности, если любое из них не выполнено. Эндпоинты данных намеренно ведут себя иначе: они продолжают возвращать последние сохранённые строки, поэтому значение ничего не значит без даты покрытия и согласующегося с ней состояния готовности. Эта страница показывает и то и другое и прямо сообщает, когда данные отстают.',
        ],
      },
      {
        heading: 'Чего модель не видит.',
        body: [
          'У неё нет ончейн-данных, новостей, глубины книги ордеров и сведений о событиях после последнего завершённого дня. Она работает с дневными барами, поэтому падение и восстановление внутри одного дня для неё невидимы. Модель предполагает, что будущее достаточно похоже на прошлое, чтобы историческое сравнение имело смысл, и это предположение нарушается именно тогда, когда оно было бы полезнее всего.',
        ],
      },
      {
        heading: 'Что происходит при изменении методологии.',
        body: [
          'Методология имеет версию — сейчас это crypto-scout-canonical-v1.1, — которую сообщают проверка готовности и лестница уровней. Изменение, влияющее на числа, получает новую строку версии, поэтому ранее записанное значение всегда можно связать с правилами, по которым оно было рассчитано.',
        ],
      },
    ],
    referenceLinkLabel: 'Открыть техническое описание методологии',
  },
  zh: {
    title: '如何阅读 Bitcoin Risk Brief',
    intro: '本指南说明每日风险数值的含义、分类方式及其局限。',
    translationNotice: '本页面为译文；英文版本为权威版本。',
    sections: [
      {
        heading: '这个数值是什么。',
        body: [
          '这是一个从 0.0 到 1.0 的单一数值，用于描述比特币市场相对于自身历史而言有多么偏离常态，并根据已完成的每日数据每天重新计算一次。它不是价格下跌的概率，不是目标价，也不是买卖任何资产的指令。它把三个观察结果压缩成一个数字，而与所有压缩一样，它舍弃的信息多于保留的信息。',
        ],
      },
      {
        heading: '为什么今天显示为低、中性或高。',
        body: [
          '低于 0.30 为低。从 0.30 起、但不包括 0.70 为中性。0.70 及以上为高。边界是固定的，因此只有当数值跨过边界时，状态才会改变。0.25 因低于 0.30 而属于低，并在达到 0.30 时变为中性，而不是在市场感觉发生变化时才改变。',
        ],
      },
      {
        heading: '它包含哪些因素。',
        body: [
          '三个输入：价格偏离长期趋势的程度、近期波动的剧烈程度，以及交易活动相对于市场规模的大小。每项输入都与其自身历史比较，而不是与绝对水平比较，因此在 2015 年可能极端的价格，如今未必极端。确切公式、权重和窗口均发布在技术参考中。',
        ],
      },
      {
        heading: '这里显示的价格不是实时报价。',
        body: [
          '它是最后一根已完成日线的 HLC3 平均值，即最高价、最低价和收盘价之和除以三。它是模型输入，不是当前市场价格，因此会与交易所此刻显示的价格不同。本页面不会在日内更新。',
        ],
      },
      {
        heading: '风险等级阶梯不是预测。',
        body: [
          '它回答的是一个反向问题：在除价格外的所有因素保持不变时，价格达到多少，模型才会报告各个风险等级？这是对模型形态的描述，不是预测、目标价、支撑线或交易建议。如果其他输入发生变化，阶梯也会随之移动。',
        ],
      },
      {
        heading: '什么时候不应信任今天的数值。',
        body: [
          '数据必须是最新的，并且必须通过验证。单独的就绪检查会报告这两项；只要任一项失败，它就会返回 HTTP 503，而不是绿色就绪信号。数据端点有意采用不同的行为：它们继续返回所保存的最新数据行，因此如果没有对应的覆盖日期和一致的就绪状态，数值本身没有意义。本页面会同时显示两者，并在数据滞后时明确说明。',
        ],
      },
      {
        heading: '模型看不到什么。',
        body: [
          '它没有链上数据、新闻、订单簿深度，也不知道最后一个已完成日期之后发生的任何事情。它使用日线，因此同一天内的下跌和反弹对它不可见。它假设未来与过去足够相似，使历史比较具有意义，而这一假设恰恰可能在最需要它时失效。',
        ],
      },
      {
        heading: '方法发生变化时会怎样。',
        body: [
          '该方法带有版本，目前为 crypto-scout-canonical-v1.1；就绪检查会报告该版本，风险等级阶梯旁也会显示。任何会改变数值的调整都会获得新的版本字符串，因此你之前记录的数值始终可以追溯到生成它的规则。',
        ],
      },
    ],
    referenceLinkLabel: '阅读技术方法参考',
  },
  de: {
    title: 'So liest du den Bitcoin Risk Brief',
    intro: 'Ein Leitfaden zur täglichen Risikozahl, ihrer Einordnung und ihren Grenzen.',
    translationNotice: 'Diese Seite ist eine Übersetzung; die englische Version ist maßgeblich.',
    sections: [
      {
        heading: 'Was diese Zahl ist.',
        body: [
          'Ein einzelner Wert von 0.0 bis 1.0, der beschreibt, wie stark der Bitcoin-Markt im Vergleich zu seiner eigenen Geschichte überdehnt wirkt. Er wird einmal täglich anhand abgeschlossener Tagesdaten neu berechnet. Er ist weder die Wahrscheinlichkeit eines Preisrückgangs noch ein Kursziel oder eine Aufforderung, etwas zu kaufen oder zu verkaufen. Er verdichtet drei Beobachtungen zu einer Zahl und verwirft wie jede Verdichtung mehr, als er bewahrt.',
        ],
      },
      {
        heading: 'Warum der heutige Wert niedrig, neutral oder hoch ist.',
        body: [
          'Unter 0.30 ist der Wert niedrig. Von 0.30 bis ausschließlich 0.70 ist er neutral. Ab 0.70 ist er hoch. Die Grenzen sind fest, daher ändert sich der Zustand nur, wenn der Wert eine Grenze überschreitet. Ein Wert von 0.25 ist niedrig, weil er unter 0.30 liegt, und wird bei 0.30 neutral — nicht in dem Moment, in dem sich der Markt anders anfühlt.',
        ],
      },
      {
        heading: 'Was einfließt.',
        body: [
          'Drei Eingaben: wie weit der Preis von seinem langfristigen Trend entfernt ist, wie heftig er sich zuletzt bewegt hat und wie groß die Handelsaktivität im Verhältnis zur Marktgröße ist. Jede Eingabe wird mit ihrer eigenen Geschichte statt mit einem absoluten Niveau verglichen. Deshalb muss ein Preis, der 2015 extrem gewesen wäre, heute nicht extrem sein. Die genauen Formeln, Gewichte und Zeitfenster sind in der technischen Referenz veröffentlicht.',
        ],
      },
      {
        heading: 'Der hier gezeigte Preis ist keine Kursnotierung.',
        body: [
          'Er ist der HLC3-Durchschnitt der letzten abgeschlossenen Tageskerze — Hoch, Tief und Schlusskurs geteilt durch drei. Er ist eine Modelleingabe, nicht der aktuelle Marktpreis, und unterscheidet sich daher von dem, was eine Börse gerade anzeigt. Auf dieser Seite wird untertägig nichts aktualisiert.',
        ],
      },
      {
        heading: 'Die Stufenleiter ist keine Prognose.',
        body: [
          'Sie beantwortet eine rückwärts gerichtete Frage: Bei welchem Preis würde das Modell die einzelnen Risikostufen melden, wenn alles außer dem Preis unverändert bliebe? Das beschreibt die Form des Modells und ist keine Vorhersage, kein Ziel, keine Unterstützungslinie und kein Handel. Wenn sich die anderen Eingaben ändern, bewegt sich die Leiter mit ihnen.',
        ],
      },
      {
        heading: 'Wann man der heutigen Zahl nicht vertrauen sollte.',
        body: [
          'Die Daten müssen aktuell sein und die Validierung bestanden haben. Eine separate Bereitschaftsprüfung meldet beides und antwortet mit HTTP 503 statt mit grünem Licht, wenn eine der Prüfungen fehlschlägt. Die Datenendpunkte verhalten sich absichtlich anders: Sie liefern weiterhin die zuletzt gespeicherten Zeilen. Ein Wert bedeutet daher nichts ohne das zugehörige Abdeckungsdatum und einen dazu passenden Bereitschaftsstatus. Diese Seite zeigt beides und weist klar darauf hin, wenn die Daten zurückliegen.',
        ],
      },
      {
        heading: 'Was das Modell nicht sehen kann.',
        body: [
          'Es kennt keine On-Chain-Daten, keine Nachrichten, keine Orderbuchtiefe und nichts, was nach dem letzten abgeschlossenen Tag geschehen ist. Es arbeitet mit Tagesbalken, sodass ein Kurssturz und eine Erholung innerhalb eines Tages unsichtbar bleiben. Es setzt voraus, dass die Zukunft der Vergangenheit ausreichend ähnelt, damit ein historischer Vergleich sinnvoll ist — und diese Annahme scheitert genau dann, wenn sie am nützlichsten wäre.',
        ],
      },
      {
        heading: 'Was bei einer Änderung der Methodik geschieht.',
        body: [
          'Die Methodik trägt eine Version, derzeit crypto-scout-canonical-v1.1, die von der Bereitschaftsprüfung und neben der Stufenleiter gemeldet wird. Eine Änderung, die die Zahlen verändert, erhält eine neue Versionszeichenfolge. So lässt sich ein früher aufgezeichneter Wert immer auf die Regeln zurückführen, die ihn erzeugt haben.',
        ],
      },
    ],
    referenceLinkLabel: 'Technische Methodik lesen',
  },
  fr: {
    title: 'Comment lire Bitcoin Risk Brief',
    intro: 'Un guide pour interpréter le chiffre de risque quotidien, sa classification et ses limites.',
    translationNotice: 'Cette page est une traduction ; la version anglaise fait autorité.',
    sections: [
      {
        heading: 'Ce que représente ce chiffre.',
        body: [
          'Une valeur unique de 0.0 à 1.0 qui décrit à quel point le marché du Bitcoin semble tendu par rapport à son propre historique, recalculée une fois par jour à partir de données quotidiennes clôturées. Ce n’est ni la probabilité que le prix baisse, ni un objectif, ni une instruction d’acheter ou de vendre quoi que ce soit. Elle condense trois observations en un seul chiffre et, comme toute condensation, écarte plus d’informations qu’elle n’en conserve.',
        ],
      },
      {
        heading: 'Pourquoi la lecture du jour est faible, neutre ou élevée.',
        body: [
          'En dessous de 0.30, elle est faible. De 0.30 jusqu’à 0.70 exclu, elle est neutre. À partir de 0.70, elle est élevée. Les seuils sont fixes : l’état ne change donc que lorsque la valeur en franchit un. Une lecture de 0.25 est faible parce qu’elle se situe sous 0.30, et elle devient neutre à 0.30 — pas au moment où le marché semble différent.',
        ],
      },
      {
        heading: 'Ce qui entre dans le calcul.',
        body: [
          'Trois entrées : l’écart du prix par rapport à sa tendance de long terme, la violence de ses mouvements récents et le niveau d’activité de négociation par rapport à la taille du marché. Chacune est comparée à son propre historique plutôt qu’à un niveau absolu ; un prix qui aurait été extrême en 2015 ne l’est donc pas nécessairement aujourd’hui. Les formules exactes, les pondérations et les fenêtres sont publiées dans la référence technique.',
        ],
      },
      {
        heading: 'Le prix affiché ici n’est pas une cotation.',
        body: [
          'Il s’agit de la moyenne HLC3 de la dernière bougie quotidienne clôturée — le plus haut, le plus bas et la clôture divisés par trois. C’est une entrée du modèle, non le prix actuel du marché, et il diffère donc de ce qu’une plateforme d’échange affiche à cet instant. Rien sur cette page ne se met à jour en cours de journée.',
        ],
      },
      {
        heading: 'L’échelle des niveaux n’est pas une prévision.',
        body: [
          'Elle répond à une question posée à l’envers : si tout sauf le prix restait fixe, à quel prix le modèle indiquerait-il chaque niveau de risque ? C’est une description de la forme du modèle, et non une prédiction, un objectif, un niveau de support ou une opération. Si les autres entrées évoluent, l’échelle évolue avec elles.',
        ],
      },
      {
        heading: 'Quand ne pas faire confiance au chiffre du jour.',
        body: [
          'Les données doivent être à jour et avoir passé la validation. Un contrôle de disponibilité séparé indique ces deux états et répond avec HTTP 503 plutôt qu’avec un feu vert si l’un d’eux échoue. Les points de terminaison de données se comportent volontairement autrement : ils continuent de renvoyer les dernières lignes qu’ils détiennent. Une valeur ne signifie donc rien sans la date couverte et un état de disponibilité concordant. Cette page affiche les deux et indique clairement lorsque les données ont pris du retard.',
        ],
      },
      {
        heading: 'Ce que le modèle ne peut pas voir.',
        body: [
          'Il ne dispose ni de données on-chain, ni d’actualités, ni de profondeur du carnet d’ordres, ni d’informations sur ce qui s’est produit après le dernier jour clôturé. Il travaille sur des barres quotidiennes : une baisse suivie d’un rebond dans la même journée lui est donc invisible. Il suppose que l’avenir ressemble suffisamment au passé pour qu’une comparaison historique ait un sens, et cette hypothèse échoue précisément lorsqu’elle serait la plus utile.',
        ],
      },
      {
        heading: 'Ce qui se passe lorsque la méthodologie change.',
        body: [
          'La méthodologie porte une version, actuellement crypto-scout-canonical-v1.1, indiquée par le contrôle de disponibilité et à côté de l’échelle des niveaux. Toute modification qui change les chiffres reçoit une nouvelle chaîne de version, afin qu’une valeur enregistrée auparavant puisse toujours être rattachée aux règles qui l’ont produite.',
        ],
      },
    ],
    referenceLinkLabel: 'Lire la méthodologie technique',
  },
  es: {
    title: 'Cómo leer Bitcoin Risk Brief',
    intro: 'Una guía para interpretar la cifra diaria de riesgo, su clasificación y sus límites.',
    translationNotice: 'Esta página es una traducción; la versión en inglés es la autoritativa.',
    sections: [
      {
        heading: 'Qué es esta cifra.',
        body: [
          'Un único valor de 0.0 a 1.0 que describe cuánto se ha alejado el mercado de Bitcoin de su comportamiento histórico, recalculado una vez al día a partir de datos diarios ya completados. No es la probabilidad de que el precio caiga, ni un objetivo, ni una instrucción para comprar o vender nada. Comprime tres observaciones en una sola cifra y, como toda compresión, descarta más de lo que conserva.',
        ],
      },
      {
        heading: 'Por qué hoy aparece como bajo, neutral o alto.',
        body: [
          'Por debajo de 0.30 es bajo. Desde 0.30 hasta 0.70, sin incluir 0.70, es neutral. 0.70 o más es alto. Los límites son fijos, por lo que el estado solo cambia cuando el valor cruza uno. Una lectura de 0.25 es baja porque está por debajo de 0.30, y pasa a ser neutral en 0.30, no en el momento en que el mercado empieza a sentirse diferente.',
        ],
      },
      {
        heading: 'Qué factores incluye.',
        body: [
          'Tres entradas: cuánto se aleja el precio de su tendencia a largo plazo, con cuánta violencia se ha movido recientemente y cuánta actividad de negociación hay en relación con el tamaño del mercado. Cada una se compara con su propio historial, no con un nivel absoluto; por eso, un precio que habría sido extremo en 2015 no tiene por qué serlo ahora. Las fórmulas, ponderaciones y ventanas exactas se publican en la referencia técnica.',
        ],
      },
      {
        heading: 'El precio mostrado aquí no es una cotización.',
        body: [
          'Es el promedio HLC3 de la última vela diaria completada: máximo, mínimo y cierre divididos entre tres. Es una entrada del modelo, no el precio actual del mercado, y será diferente de lo que muestre una plataforma de intercambio en este momento. Nada de esta página se actualiza durante el día.',
        ],
      },
      {
        heading: 'La escala de niveles no es un pronóstico.',
        body: [
          'Responde una pregunta inversa: si todo salvo el precio se mantuviera fijo, ¿a qué precio indicaría el modelo cada nivel de riesgo? Es una descripción de la forma del modelo, no una predicción, un objetivo, una línea de soporte ni una operación. Si cambian las demás entradas, la escala cambia con ellas.',
        ],
      },
      {
        heading: 'Cuándo no confiar en la cifra de hoy.',
        body: [
          'Los datos deben estar actualizados y haber superado la validación. Una comprobación de disponibilidad separada informa de ambas cosas y responde con HTTP 503 en lugar de dar luz verde cuando alguna falla. Los endpoints de datos se comportan de otra forma a propósito: siguen devolviendo las últimas filas que conservan. Por eso, un valor no significa nada sin la fecha cubierta y un estado de disponibilidad que coincida. Esta página muestra ambos y avisa claramente cuando los datos se han quedado atrás.',
        ],
      },
      {
        heading: 'Qué no puede ver el modelo.',
        body: [
          'No tiene datos on-chain, noticias, profundidad del libro de órdenes ni conocimiento de nada que haya ocurrido después del último día completado. Trabaja con barras diarias, por lo que una caída y recuperación dentro del mismo día son invisibles para él. Supone que el futuro se parece al pasado lo suficiente como para que una comparación histórica tenga sentido, y esa suposición falla precisamente cuando sería más útil.',
        ],
      },
      {
        heading: 'Qué ocurre cuando cambia la metodología.',
        body: [
          'La metodología lleva una versión, actualmente crypto-scout-canonical-v1.1, que se informa en la comprobación de disponibilidad y junto a la escala de niveles. Un cambio que altere las cifras recibe una nueva cadena de versión, de modo que cualquier valor registrado anteriormente siempre pueda vincularse con las reglas que lo produjeron.',
        ],
      },
    ],
    referenceLinkLabel: 'Leer la metodología técnica',
  },
  ar: {
    title: 'كيفية قراءة Bitcoin Risk Brief',
    intro: 'دليل لتفسير رقم المخاطر اليومي وتصنيفه وحدود ما يمكنه إظهاره.',
    translationNotice: 'هذه الصفحة ترجمة؛ والنسخة الإنجليزية هي النسخة المعتمدة.',
    sections: [
      {
        heading: 'ما هو هذا الرقم.',
        body: [
          'قيمة واحدة من 0.0 إلى 1.0 تصف مدى ابتعاد سوق بيتكوين عن نمطه التاريخي، ويُعاد حسابها مرة يوميًا من بيانات يومية مكتملة. وهي ليست احتمالًا لانخفاض السعر، ولا سعرًا مستهدفًا، ولا تعليمات لشراء أي شيء أو بيعه. فهي تضغط ثلاث ملاحظات في رقم واحد، وكأي عملية ضغط تستبعد معلومات أكثر مما تحتفظ به.',
        ],
      },
      {
        heading: 'لماذا تُصنَّف قراءة اليوم منخفضة أو محايدة أو مرتفعة.',
        body: [
          'ما دون 0.30 منخفض. ومن 0.30 حتى 0.70 دون تضمين 0.70 محايد. و0.70 فما فوق مرتفع. الحدود ثابتة، لذلك لا تتغير الحالة إلا عندما تتجاوز القيمة أحدها. قراءة 0.25 منخفضة لأنها أدنى من 0.30، وتصبح محايدة عند 0.30، لا في اللحظة التي يبدو فيها السوق مختلفًا.',
        ],
      },
      {
        heading: 'ما الذي يدخل في الحساب.',
        body: [
          'ثلاثة مدخلات: مدى ابتعاد السعر عن اتجاهه طويل الأجل، ومدى حدة تحركه مؤخرًا، وحجم نشاط التداول نسبةً إلى حجم السوق. يُقارن كل مدخل بتاريخه الخاص بدلًا من مستوى مطلق، ولذلك ليس بالضرورة أن يكون السعر الذي كان سيُعد متطرفًا في 2015 متطرفًا الآن. تُنشر الصيغ والأوزان والنوافذ الدقيقة في المرجع التقني.',
        ],
      },
      {
        heading: 'السعر المعروض هنا ليس عرض سعر مباشرًا.',
        body: [
          'إنه متوسط HLC3 لآخر شمعة يومية مكتملة، أي أعلى سعر وأدنى سعر وسعر الإغلاق مقسومة على ثلاثة. وهو مدخل للنموذج، وليس سعر السوق الحالي، وسيختلف عما تعرضه منصة التداول الآن. لا يتم تحديث أي شيء في هذه الصفحة خلال اليوم.',
        ],
      },
      {
        heading: 'سُلّم المستويات ليس توقعًا.',
        body: [
          'إنه يجيب عن سؤال عكسي: مع تثبيت كل شيء عدا السعر، عند أي سعر سيعرض النموذج كل مستوى من مستويات المخاطر؟ هذا وصف لشكل النموذج، وليس تنبؤًا أو هدفًا أو خط دعم أو صفقة. وإذا تحركت المدخلات الأخرى، يتحرك السُلّم معها.',
        ],
      },
      {
        heading: 'متى ينبغي عدم الوثوق برقم اليوم.',
        body: [
          'يجب أن تكون البيانات حديثة وأن تكون قد اجتازت التحقق. يبلّغ فحص جاهزية منفصل عن الأمرين، ويرد بحالة HTTP 503 بدلًا من إشارة خضراء إذا فشل أي منهما. وتتصرف نقاط نهاية البيانات بصورة مختلفة عن قصد: فهي تواصل إعادة آخر الصفوف المحفوظة لديها، لذلك لا تعني القيمة شيئًا من دون تاريخ التغطية الموافق لها وحالة جاهزية متسقة معه. تعرض هذه الصفحة الأمرين وتوضح صراحةً عندما تتأخر البيانات.',
        ],
      },
      {
        heading: 'ما الذي لا يستطيع النموذج رؤيته.',
        body: [
          'لا يملك بيانات على السلسلة، ولا أخبارًا، ولا عمق دفتر الأوامر، ولا معرفة بأي شيء حدث بعد آخر يوم مكتمل. وهو يعمل على أشرطة يومية، لذلك لا يرى هبوطًا وتعافيًا يحدثان داخل يوم واحد. يفترض أن المستقبل يشبه الماضي بما يكفي ليكون للمقارنة التاريخية معنى، ويفشل هذا الافتراض تحديدًا عندما يكون في أمسّ الحاجة إليه.',
        ],
      },
      {
        heading: 'ما الذي يحدث عند تغيير المنهجية.',
        body: [
          'تحمل المنهجية إصدارًا، وهو حاليًا crypto-scout-canonical-v1.1، ويبلّغ عنه فحص الجاهزية ويظهر بجانب سُلّم المستويات. ويحصل أي تغيير يعدّل الأرقام على سلسلة إصدار جديدة، بحيث يمكن دائمًا تتبع أي قيمة سجلتها سابقًا إلى القواعد التي أنتجتها.',
        ],
      },
    ],
    referenceLinkLabel: 'قراءة المنهجية التقنية',
  },
}
