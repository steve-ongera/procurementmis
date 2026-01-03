import random
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from pms.models import (
    Requisition,
    RequisitionItem,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceivedNote,
    GRNItem,
    StockItem,
    StockMovement,
    Invoice,
    InvoiceItem,
    Payment,
    Supplier,
    Store,
    Item
)

from django.contrib.auth import get_user_model
User = get_user_model()


class Command(BaseCommand):
    help = "Create POs for requisitions without POs (3-year historical data)"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Seeding Purchase Orders...")

        suppliers = list(Supplier.objects.all())
        users = list(User.objects.all())
        stores = list(Store.objects.all())

        if not suppliers or not users or not stores:
            self.stdout.write(self.style.ERROR(
                "❌ Suppliers, Users, or Stores missing."
            ))
            return

        today = timezone.now()
        start_date = today - timedelta(days=365 * 3)

        requisitions = Requisition.objects.filter(
            purchase_orders__isnull=True,
            status__in=["APPROVED", "PROCUREMENT_APPROVED"]
        )

        created_count = 0

        for req in requisitions:
            created_at = start_date + timedelta(
                days=random.randint(0, 365 * 3)
            )

            supplier = random.choice(suppliers)
            created_by = random.choice(users)

            subtotal = sum(
                item.estimated_total for item in req.items.all()
            )

            tax = subtotal * Decimal("0.16")
            total = subtotal + tax

            po = PurchaseOrder.objects.create(
                requisition=req,
                supplier=supplier,
                delivery_date=(created_at + timedelta(days=14)).date(),
                delivery_address="Main University Stores, Nairobi Campus",
                subtotal=subtotal,
                tax_amount=tax,
                total_amount=total,
                payment_terms="Payment within 30 days after delivery",
                warranty_terms="12 months warranty",
                special_instructions="Deliver during working hours",
                status=random.choice([
                    "APPROVED",
                    "SENT",
                    "DELIVERED",
                    "CLOSED"
                ]),
                approved_by=random.choice(users),
                approved_at=created_at + timedelta(days=1),
                sent_at=created_at + timedelta(days=2),
                created_by=created_by,
            )

            PurchaseOrder.objects.filter(id=po.id).update(
                created_at=created_at,
                updated_at=created_at + timedelta(days=2),
            )

            # ================= PO ITEMS =================
            for req_item in req.items.all():
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    requisition_item=req_item,
                    item_description=req_item.item_description,
                    specifications=req_item.specifications,
                    quantity=req_item.quantity,
                    unit_of_measure=req_item.unit_of_measure,
                    unit_price=req_item.estimated_unit_price,
                    quantity_delivered=req_item.quantity,
                )

            # ================= GRN =================
            store = random.choice(stores)

            grn = GoodsReceivedNote.objects.create(
                purchase_order=po,
                store=store,
                delivery_note_number=f"DN-{random.randint(1000,9999)}",
                delivery_date=(created_at + timedelta(days=14)).date(),
                received_by=random.choice(users),
                inspected_by=random.choice(users),
                inspection_date=(created_at + timedelta(days=15)).date(),
                status="ACCEPTED",
                general_condition="Goods received in good condition",
            )

            GoodsReceivedNote.objects.filter(id=grn.id).update(
                created_at=created_at + timedelta(days=14)
            )

            # ================= GRN ITEMS + STOCK =================
            for po_item in po.items.all():
                GRNItem.objects.create(
                    grn=grn,
                    po_item=po_item,
                    quantity_ordered=po_item.quantity,
                    quantity_delivered=po_item.quantity,
                    quantity_accepted=po_item.quantity,
                )

                stock_item, _ = StockItem.objects.get_or_create(
                    store=store,
                    item=po_item.requisition_item.item,
                    defaults={
                        "quantity_on_hand": 0,
                        "average_unit_cost": po_item.unit_price,
                    }
                )

                balance_before = stock_item.quantity_on_hand
                stock_item.quantity_on_hand += po_item.quantity
                stock_item.total_value = (
                    stock_item.quantity_on_hand * stock_item.average_unit_cost
                )
                stock_item.last_restock_date = grn.delivery_date
                stock_item.save()

                StockMovement.objects.create(
                    stock_item=stock_item,
                    movement_type="RECEIPT",
                    reference_number=grn.grn_number,
                    reference_type="GRN",
                    quantity=po_item.quantity,
                    unit_cost=po_item.unit_price,
                    balance_before=balance_before,
                    balance_after=stock_item.quantity_on_hand,
                    to_store=store,
                    performed_by=random.choice(users),
                )

            # ================= INVOICE =================
            invoice = Invoice.objects.create(
                invoice_number=f"INV-{random.randint(100000,999999)}",
                supplier_invoice_number=f"SINV-{random.randint(1000,9999)}",
                purchase_order=po,
                grn=grn,
                supplier=supplier,
                invoice_date=created_at.date(),
                due_date=(created_at + timedelta(days=30)).date(),
                subtotal=subtotal,
                tax_amount=tax,
                total_amount=total,
                status="PAID",
                is_three_way_matched=True,
                verified_by=random.choice(users),
                verified_at=created_at + timedelta(days=1),
                approved_by=random.choice(users),
                approved_at=created_at + timedelta(days=2),
                submitted_by=random.choice(users),
            )

            for po_item in po.items.all():
                InvoiceItem.objects.create(
                    invoice=invoice,
                    po_item=po_item,
                    description=po_item.item_description,
                    quantity=po_item.quantity,
                    unit_price=po_item.unit_price,
                    tax_rate=Decimal("16.00"),
                )

            # ================= PAYMENT =================
            Payment.objects.create(
                invoice=invoice,
                payment_date=(created_at + timedelta(days=28)).date(),
                payment_amount=total,
                payment_method=random.choice([
                    "BANK_TRANSFER",
                    "EFT",
                    "CHEQUE"
                ]),
                payment_reference=f"PAYREF-{random.randint(100000,999999)}",
                bank_name="KCB Bank Kenya",
                status="COMPLETED",
                processed_by=random.choice(users),
                approved_by=random.choice(users),
            )

            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Created POs for {created_count} requisitions (3-year range)"
        ))
