import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent as ReactKeyboardEvent } from 'react'
import { Languages } from 'lucide-react'
import type { LocaleOption } from './locales'
import type { Locale } from './types'

type LanguageSelectProps = {
  label: string
  locale: Locale
  options: readonly LocaleOption[]
  onLocaleChange: (locale: Locale) => void
}

function wrappedIndex(index: number, length: number) {
  return (index + length) % length
}

function optionId(listboxId: string, option: LocaleOption) {
  return `${listboxId}-${option.code}`
}

export function LanguageSelect({ label, locale, options, onLocaleChange }: LanguageSelectProps) {
  const listboxId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const listboxRef = useRef<HTMLUListElement>(null)
  const selectedIndex = Math.max(options.findIndex((option) => option.code === locale), 0)
  const selectedOption = options[selectedIndex] ?? options[0]
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(selectedIndex)
  const activeOption = options[activeIndex] ?? selectedOption

  useEffect(() => {
    if (!open) setActiveIndex(selectedIndex)
  }, [open, selectedIndex])

  useEffect(() => {
    if (!open) return
    listboxRef.current?.focus()
  }, [open])

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target
      if (target && rootRef.current && !rootRef.current.contains(target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [open])

  const selectedLabel = useMemo(() => `${label}: ${selectedOption.label}`, [label, selectedOption.label])

  const openMenu = (nextActiveIndex = selectedIndex) => {
    setActiveIndex(nextActiveIndex)
    setOpen(true)
  }

  const selectOption = (option: LocaleOption) => {
    onLocaleChange(option.code)
    setOpen(false)
    buttonRef.current?.focus()
  }

  const handleButtonKeyDown = (event: ReactKeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openMenu(selectedIndex)
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      openMenu(wrappedIndex(selectedIndex + 1, options.length))
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      openMenu(wrappedIndex(selectedIndex - 1, options.length))
    }
  }

  const handleListboxKeyDown = (event: ReactKeyboardEvent<HTMLUListElement>) => {
    if (event.key === 'Tab') {
      setOpen(false)
      return
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((index) => wrappedIndex(index + 1, options.length))
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((index) => wrappedIndex(index - 1, options.length))
    }

    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      selectOption(activeOption)
    }

    if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
      buttonRef.current?.focus()
    }
  }

  return (
    <div className="language-select" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="language-trigger"
        aria-label={selectedLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listboxId : undefined}
        onClick={() => (open ? setOpen(false) : openMenu(selectedIndex))}
        onKeyDown={handleButtonKeyDown}
      >
        <Languages size={16} aria-hidden="true" />
        <span className="language-code" aria-hidden="true">{selectedOption.code.toUpperCase()}</span>
      </button>
      {open ? (
        <ul
          ref={listboxRef}
          id={listboxId}
          className="language-menu"
          role="listbox"
          aria-label={label}
          aria-activedescendant={optionId(listboxId, activeOption)}
          tabIndex={-1}
          onKeyDown={handleListboxKeyDown}
        >
          {options.map((option, index) => (
            <li
              key={option.code}
              id={optionId(listboxId, option)}
              className={`language-option${index === activeIndex ? ' is-active' : ''}`}
              role="option"
              aria-selected={option.code === locale}
              onClick={() => selectOption(option)}
              onMouseMove={() => setActiveIndex(index)}
            >
              <bdi dir="ltr">{option.shortLabel}</bdi>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
