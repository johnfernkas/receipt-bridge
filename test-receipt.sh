#!/usr/bin/env bash
# Usage: ./test-receipt.sh <host> [port]
HOST=${1:?usage: $0 <host> [port]}
PORT=${2:-9100}

{
  printf '\x1b\x40'               # init

  printf '\x1b\x61\x01'          # center
  printf '\x1b\x45\x01\x1d\x21\x11'
  printf 'CORNER CAFE\n'
  printf '\x1d\x21\x00\x1b\x45\x00'
  printf '123 Main Street\n'
  printf 'Springfield, USA\n'
  printf 'Tel: 555-123-4567\n\n'

  printf '\x1b\x61\x00'          # left
  printf -- '----------------------------------------\n'
  printf 'Table 4                    Server: Alex\n'
  printf '05/14/2026                   10:32 AM\n'
  printf -- '----------------------------------------\n'
  printf 'Drip Coffee                          $2.50\n'
  printf 'Avocado Toast                        $9.00\n'
  printf 'Orange Juice                         $4.00\n'
  printf 'Blueberry Muffin                     $3.50\n'
  printf -- '----------------------------------------\n'
  printf 'Subtotal:                           $19.00\n'
  printf 'Tax (8%%):                            $1.52\n'
  printf -- '----------------------------------------\n'
  printf '\x1b\x45\x01'
  printf 'TOTAL:                              $20.52\n'
  printf '\x1b\x45\x00'
  printf -- '----------------------------------------\n'

  printf '\x1b\x61\x01'          # center
  printf '\nThank you for visiting!\nPlease come again!\n'

  printf '\x1b\x64\x05'          # feed + cut
  printf '\x1d\x56\x01'

} | nc -w1 "$HOST" "$PORT"
