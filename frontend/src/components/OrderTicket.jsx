import { usd, krw, qty } from '../format.js'

export default function OrderTicket({ order, kind }) {
  const priceText = order.price_usd == null ? '종가 매도' : '주당 ' + usd(order.price_usd)
  const amtUsd = order.amount_usd == null ? '' : usd(order.amount_usd)
  const amtKrw = order.amount_krw == null ? '' : krw(order.amount_krw)
  const amt = [amtUsd, amtKrw].filter(Boolean).join(' · ')
  return (
    <div className={'ticket ' + kind}>
      <div className="ticket-l">
        <div className="ticket-label">{order.label}</div>
        <div className="ticket-meta">
          {order.order_type}{order.note ? ' · ' + order.note : ''}
        </div>
      </div>
      <div className="ticket-r">
        <div className="ticket-qty num">{qty(order.quantity)}</div>
        <div className="ticket-price num">{priceText}</div>
        {amt && <div className="ticket-amt num">{amt}</div>}
      </div>
    </div>
  )
}
