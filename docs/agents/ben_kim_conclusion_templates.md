# Ben_Kim Conclusion Templates

## Status
Final baseline.

## Purpose
Канонический reference для построения conclusions `Ben_Kim`.

Документ фиксирует:
- общую формулу conclusion;
- strategy-specific templates;
- weak-signal wording;
- forbidden wording;
- confidence discipline constraints.

---

## Canonical conclusion formula

Каждый conclusion должен строиться по логике:

`Observation -> Implication -> Confidence Discipline`

Где:
- **Observation** = что реально видно в данных;
- **Implication** = что это значит в рамках стратегии;
- **Confidence Discipline** = ограничитель силы формулировки.

### Core rule
Сила conclusion не должна превышать силу evidence.

---

## Global wording rules

### Preferred wording
Предпочтительно использовать:
- "остаётся"
- "выглядит как"
- "указывает на"
- "пока"
- "не подтверждён"
- "ограниченный edge"
- "смешанный контекст"
- "candidate"
- "correction"
- "давление сохраняется"

### Forbidden wording
Запрещено использовать как стандартную аналитику:
- "точно"
- "гарантированно"
- "обязательно"
- "явный разворот" без подтверждения
- "подтверждённый сценарий" при weak evidence
- "рынок точно пойдёт"
- deterministic language for heuristic layers

---

## 1. price_levels_fibo_horizontal_volume

### Template A — neutral structural context
Observation: цена находится относительно POC / value area / support-resistance / nearest fib.
Implication: structural context neutral / mixed / weakly supportive / weakly pressuring.
Confidence Discipline: явного подтверждённого directional edge пока нет.

**Ready-form wording:**
- "Цена находится [относительно POC / value area / fib / support-resistance]; структурный контекст [neutral/mixed/weakly supportive/weakly pressuring], явного directional edge пока нет."

### Template B — support leaning
Observation: цена удерживается у поддержки / внутри value area / рядом с значимым fib-level.
Implication: структура даёт локальную поддержку.
Confidence Discipline: без подтверждения потоком или импульсом это ещё не сильный разворотный сигнал.

**Ready-form wording:**
- "Цена удерживается у значимой зоны поддержки / внутри value area; структура локально поддерживает цену, но подтверждённого разворота пока нет."

### Template C — pressure / weakness
Observation: цена ниже POC / под сопротивлением / ниже значимого fib-level.
Implication: structural context остаётся слабым.
Confidence Discipline: давление вниз видно, но силу сигнала нужно подтверждать другими слоями.

**Ready-form wording:**
- "Цена торгуется ниже объёмного центра / под значимой зоной; структурный контекст остаётся слабым, давление вниз сохраняется без полного подтверждения разворота."

### Template D — confluence
Observation: support/resistance, fib и horizontal volume сходятся в одной зоне.
Implication: зона структурно значима.
Confidence Discipline: confluence повышает значимость уровня, но не гарантирует реакцию цены.

**Ready-form wording:**
- "В зоне сходятся структурный уровень, fib и horizontal volume; зона значима, но сама confluence ещё не гарантирует реакцию цены."

---

## 2. vertical_volume

### Template A — confirmation
Observation: объём повышен / дельта смещена / dominance одной стороны читается.
Implication: объём подтверждает текущее движение.
Confidence Discipline: подтверждение есть, но это не гарантия продолжения.

**Ready-form wording:**
- "Объём и дельта подтверждают текущее движение; dominance одной стороны читается, но это ещё не гарантия продолжения."

### Template B — no confirmation
Observation: объём слабый / дельта смешанная / imbalance не даёт явного перекоса.
Implication: объём не подтверждает directional move.
Confidence Discipline: сигнал остаётся слабым или нейтральным.

**Ready-form wording:**
- "Объёмный слой не даёт уверенного directional подтверждения; поток остаётся смешанным, сигнал ограничен."

### Template C — seller dominance
Observation: объёмный поток смещён в продавца, дельта отрицательная.
Implication: продавец доминирует в текущем окне.
Confidence Discipline: dominance видна, но её устойчивость нужно оценивать вместе с другими стратегиями.

**Ready-form wording:**
- "Объёмный поток смещён в продавца, отрицательная дельта подтверждает давление; dominance видна, но её устойчивость требует контекстного подтверждения."

### Template D — buyer dominance
Observation: объёмный поток смещён в покупателя, дельта положительная.
Implication: покупатель доминирует в текущем окне.
Confidence Discipline: dominance видна, но без дополнительного контекста это ещё не strong break scenario.

**Ready-form wording:**
- "Объёмный поток смещён в покупателя, положительная дельта подтверждает инициативу; dominance видна, но не равна гарантированному продолжению."

---

## 3. rsi_macd

### Template A — bearish momentum
Observation: RSI слабый / oversold, MACD histogram отрицательная.
Implication: momentum остаётся медвежьим.
Confidence Discipline: перепроданность сама по себе не означает разворот.

**Ready-form wording:**
- "RSI находится в слабой / oversold зоне, MACD histogram остаётся отрицательной; momentum остаётся медвежьим, разворот пока не подтверждён."

### Template B — bullish momentum
Observation: RSI выше нейтральной зоны, MACD положительная / улучшается.
Implication: momentum остаётся бычьим.
Confidence Discipline: положительный импульс есть, но силу продолжения нужно подтверждать контекстом.

**Ready-form wording:**
- "RSI удерживается выше нейтральной зоны, MACD остаётся положительной / улучшается; momentum остаётся бычьим, но продолжение требует контекстного подтверждения."

### Template C — reversal candidate
Observation: RSI в экстремальной зоне, histogram улучшается / slope становится лучше.
Implication: появляется ранний reversal candidate.
Confidence Discipline: это кандидат, а не подтверждённый разворот.

**Ready-form wording:**
- "RSI остаётся в экстремальной зоне, но MACD histogram улучшается; появляется ранний reversal candidate, однако подтверждённого разворота ещё нет."

### Template D — neutral/mixed
Observation: RSI и MACD не дают согласованного сигнала.
Implication: momentum mixed / neutral.
Confidence Discipline: directional edge ограничен.

**Ready-form wording:**
- "RSI и MACD не дают согласованного directional сигнала; momentum остаётся смешанным, edge ограничен."

---

## 4. trade_speed

### Template A — bearish pressure
Observation: скорость сделок выше средней, imbalance отрицательный / sell-side доминирует.
Implication: поток подтверждает давление продавца.
Confidence Discipline: сама скорость без directional context не была бы сигналом; здесь важен именно перекос потока.

**Ready-form wording:**
- "Скорость сделок выше средней, а поток смещён в продавца; trade-speed слой подтверждает давление вниз, при этом ключевым фактором остаётся directional imbalance, а не одна скорость."

### Template B — bullish pressure
Observation: скорость сделок выше средней, imbalance положительный / buy-side доминирует.
Implication: поток подтверждает активность покупателя.
Confidence Discipline: это подтверждение потока, а не самостоятельный трендовый прогноз.

**Ready-form wording:**
- "Скорость сделок выше средней, поток смещён в покупателя; trade-speed слой поддерживает бычью инициативу, но сам по себе не заменяет подтверждение другими стратегиями."

### Template C — active but unclear
Observation: активность повышена, но directional imbalance слабый или смешанный.
Implication: рынок активен, но edge неочевиден.
Confidence Discipline: высокая скорость без направления не даёт сильного сигнала.

**Ready-form wording:**
- "Активность повышена, но directional imbalance остаётся слабым / смешанным; рынок активен, однако явный edge не формируется."

### Template D — slow / decelerating
Observation: скорость сделок ниже средней или поток затухает.
Implication: текущее движение не получает сильной потоковой поддержки.
Confidence Discipline: это признак ослабления активности, а не обязательно разворота.

**Ready-form wording:**
- "Скорость сделок снижается / остаётся ниже средней; потоковая поддержка движения ослаблена, но это ещё не означает разворот."

---

## 5. added_later_placeholder

### Template
Observation: стратегия не реализована.
Implication: аналитический вывод не формируется.
Confidence Discipline: сигнал отсутствует.

**Ready-form wording:**
- "Стратегия не реализована; аналитический вывод не формируется."

---

## 6. elliott_waves

### Template A — correction
Observation: Elliott block описывает correction / unclear wave structure.
Implication: рынок выглядит коррекционным, а не импульсным.
Confidence Discipline: волновой контекст остаётся heuristic и не должен трактоваться как подтверждённый сценарий.

**Ready-form wording:**
- "Волновая структура остаётся коррекционной / неясной; импульсный сценарий не подтверждён, а вывод сохраняет heuristic характер."

### Template B — weak candidate
Observation: есть candidate structure / tentative wave count.
Implication: можно рассматривать слабый сценарий продолжения или завершения коррекции.
Confidence Discipline: это лишь candidate, без права на жёсткое сценарное утверждение.

**Ready-form wording:**
- "В Elliott-слое просматривается слабый candidate-сценарий; он допускает направленную интерпретацию, но остаётся предварительным и не подтверждённым."

### Template C — no confirmed impulse
Observation: wave structure не даёт убедительной импульсной картины.
Implication: подтверждённой волновой направленности нет.
Confidence Discipline: любые directional сценарии остаются предварительными.

**Ready-form wording:**
- "Убедительной импульсной волновой структуры не видно; directional wave-сценарий не подтверждён и остаётся предварительным."

### Template D — unclear structure
Observation: Elliott block семантически слабый или неоднозначный.
Implication: волновая интерпретация ограниченно полезна.
Confidence Discipline: вывод должен оставаться осторожным и вторичным по значимости.

**Ready-form wording:**
- "Волновой контекст остаётся неоднозначным; Elliott-слой в текущем окне имеет ограниченную аналитическую полезность и требует осторожной интерпретации."

---

## Additional signal discipline reminders

### Do not do
- jump from observation to deterministic forecast;
- replace candidate with confirmed scenario;
- inflate weak evidence;
- hide partial/unclear context behind strong wording.

### Always do
- keep wording concise;
- keep wording strategy-specific;
- preserve observation basis;
- preserve strength guard.
