#!/usr/bin/env bash
# Usage: ./test-receipt.sh <host> [port]
# Example: ./test-receipt.sh 192.168.1.87
HOST=${1:?usage: $0 <host> [port]}
PORT=${2:-9100}

{
  # Initialize printer
  printf '\x1b\x40'

  # ── Header (centered) ────────────────────────────────────────────────────
  printf '\x1b\x61\x01'          # center align
  printf '\x1b\x45\x01'          # bold on
  printf '\x1d\x21\x11'          # double height + width
  printf 'CORNER CAFE\n'
  printf '\x1d\x21\x00'          # normal size
  printf '\x1b\x45\x00'          # bold off
  printf '123 Main Street\n'
  printf 'Springfield, USA\n'
  printf 'Tel: 555-123-4567\n'
  printf '\n'

  # ── Order info (left aligned) ─────────────────────────────────────────────
  printf '\x1b\x61\x00'          # left align
  printf -- '----------------------------------------\n'
  printf 'Table 4                    Server: Alex\n'
  printf '05/14/2026                   10:32 AM\n'
  printf -- '----------------------------------------\n'

  # ── Line items ────────────────────────────────────────────────────────────
  printf 'Drip Coffee                          $2.50\n'
  printf 'Avocado Toast                        $9.00\n'
  printf 'Orange Juice                         $4.00\n'
  printf 'Blueberry Muffin                     $3.50\n'
  printf -- '----------------------------------------\n'

  # ── Totals ────────────────────────────────────────────────────────────────
  printf 'Subtotal:                           $19.00\n'
  printf 'Tax (8%%):                            $1.52\n'
  printf -- '----------------------------------------\n'
  printf '\x1b\x45\x01'          # bold on
  printf 'TOTAL:                              $20.52\n'
  printf '\x1b\x45\x00'          # bold off
  printf -- '----------------------------------------\n'

  # ── Footer (centered) ─────────────────────────────────────────────────────
  printf '\x1b\x61\x01'          # center align
  printf '\n'
  printf 'Thank you for visiting!\n'
  printf 'Please come again!\n'

  # ── Feed and partial cut ──────────────────────────────────────────────────
  printf '\x1b\x64\x05'          # feed 5 lines
  printf '\x1d\x56\x01'          # partial cut

} | nc -w1 "$HOST" "$PORT"
