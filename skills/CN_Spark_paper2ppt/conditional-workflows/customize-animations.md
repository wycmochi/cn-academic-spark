---
description: Customize default PPTX animations with per-slide and per-object timing, transition, and reveal overrides.
---

# Customize Animations Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在用户要求动画、逐步出现、转场或演示节奏控制时读取；它指导基于真实 SVG group id 创建或修改 animations.json，并重新导出 PPTX。

Standalone post-generation workflow. Run only when the user asks to tune animation order, effects, timing, slide transitions, or object-level reveals. Normal PPTX export can already use global animations; this workflow creates or edits `animations.json` only when finer control is required.

## When To Run

| Condition | Action |
|---|---|
| User asks for object-level animation, reveal order, timing, pacing, or transition changes | Run this workflow. |
| User only wants the default animated deck | Do not run this workflow. |
| `<project_path>/svg_output/*.svg` is missing | Complete the main Executor phase first. |
| `<project_path>/animations.json` exists | Validate and edit it; do not overwrite unless the user asks. |

Academic decks should use restrained motion. Prefer `appear`, `fade`, and `wipe`. Avoid playful effects, excessive object reveals, and motion that distracts from source figures, formulas, citations, or TechnicalRoute diagrams.

## Step 1 - Build Or Validate The Scaffold

Use real SVG group ids. Do not invent slide keys or group ids.

If `animations.json` does not exist:

```bash
python3 scripts/animation_config.py scaffold <project_path>
```

If it already exists:

```bash
python3 scripts/animation_config.py validate <project_path>
```

The scaffold is the only valid target list. If a logical object lacks a group id, update the SVG deliberately and re-run validation instead of guessing an id.

## Step 2 - Read Semantic Context

Before editing `animations.json`, read:

| File | Use |
|---|---|
| `<project_path>/design_spec.md` | Slide intent, academic route, content type, title claim, and visual role. |
| `<project_path>/spec_lock.md` | Page rhythm, layout source, chart references, TechnicalRoute pages, footer / citation constraints. |
| `<project_path>/notes/total.md` or `<project_path>/notes/*.md` | Speaker flow, reveal order, emphasis timing. |
| `<project_path>/svg_output/*.svg` | Actual valid group ids and page stems. |

Semantic files determine animation intent. SVG files determine valid animation targets. Never reference a slide or group id absent from the scaffold or SVG scan.

If `design_spec.md` and `spec_lock.md` are both missing, do not infer detailed object choreography. Use conservative defaults and explicit user instructions only.

## Step 3 - Academic Animation Constraints

Do not animate citation footers, page numbers, bottom banners, school logos, recurring template chrome, reference-page entries line by line, individual characters or words, formula glyphs inside one formula image, or dense table cells one by one.

Animate logical groups only: title or section marker, main source figure, formula panel, chart, key interpretation rail, TechnicalRoute major stage group, or summary takeaway.

For TechnicalRoute pages:

- Version A editable template page may reveal major stages in route order.
- Version B AI reference page should usually appear as one image, followed by a short caption or takeaway.
- Do not animate every route node unless the user explicitly wants a teaching-style walkthrough.

## Step 4 - Plan Page-Level And Object-Level Motion

Plan both page transitions and in-slide object entrances before editing `animations.json`.

| Layer | Config path | Use |
|---|---|---|
| Page transition | `defaults.transition` or `slides.<slide>.transition` | How a slide enters from the previous slide. |
| Slide animation defaults | `defaults.animation` or `slides.<slide>.animation` | Default entrance behavior for animated groups. |
| Object overrides | `slides.<slide>.groups.<group_id>` | Order, effect, delay, duration, or exclusion for a real SVG group. |

Use `page_rhythm`:

| Page rhythm | Transition duration | Object duration | Stagger |
|---|---:|---:|---:|
| `anchor` | 0.35-0.60s | 0.45-0.75s | 0.20-0.40s |
| `breathing` | 0.25-0.45s | 0.40-0.65s | 0.16-0.30s |
| `dense` | 0.18-0.35s | 0.25-0.45s | 0.10-0.24s |
| key insight / final takeaway | 0.30-0.50s | 0.50-0.80s | 0.25-0.45s |

Use shorter timing for repeated technical evidence pages. Use longer timing only for conceptual pivots, route diagrams, section openers, and final takeaways.

## Step 5 - Supported Effects

Page transitions: `none`, `fade`, `push`, `wipe`, `split`, `strips`, `cover`, `random`.

In-slide entrance effects: `none`, `appear`, `fade`, `fly`, `cut`, `zoom`, `wipe`, `split`, `blinds`, `checkerboard`, `dissolve`, `random_bars`, `peek`, `wheel`, `box`, `circle`, `diamond`, `plus`, `strips`, `wedge`, `stretch`, `expand`, `swivel`, `mixed`, `random`.

Academic default:

- transition: `fade`;
- object entrance: `fade` or `wipe`;
- trigger: `after-previous`.

Use `on-click` only when the presenter explicitly wants manual pacing. Do not use `on-click` when exporting narrated PPTX with recorded audio.

## Step 6 - Edit `animations.json`

Write only overrides that differ from global defaults. Unmentioned groups keep normal export behavior.

Allowed fields:

| Field | Behavior |
|---|---|
| `transition.effect` | Slide-specific transition. |
| `transition.duration` | Slide transition duration in seconds. |
| `animation.effect` | Slide-specific default object entrance. |
| `animation.duration` | Object entrance duration in seconds. |
| `animation.stagger` | Delay between object entrances. |
| `animation.trigger` | `after-previous`, `with-previous`, or `on-click`. |
| `groups.<id>.effect` | Object-specific effect or `none`. |
| `groups.<id>.order` | Animation order only; does not change SVG z-order. |
| `groups.<id>.delay` | Extra delay before the group starts. |
| `groups.<id>.duration` | Per-group duration. |

Do not add animation attributes to SVG files. Animation customization belongs in `animations.json`.

## Step 7 - Validate And Export

Run sequentially:

```bash
python3 scripts/animation_config.py validate <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

If validation fails, fix the invalid slide key or group id. Do not suppress missing-target warnings.

## Completion Checklist

- [ ] `animations.json` exists only because custom animation was requested.
- [ ] `design_spec.md`, `spec_lock.md`, and speaker notes were checked.
- [ ] Page transitions and object entrances were planned together.
- [ ] Citation footers, page numbers, bottom banners, logos, and recurring chrome are not animated.
- [ ] TechnicalRoute pages use stage-level motion at most.
- [ ] `animation_config.py validate` passed.
- [ ] PPTX re-export completed.
