from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class GadaiTransaksi(models.Model):
    _name = 'gadai.transaksi'
    _description = 'Transaksi Gadai'

    name = fields.Char(string='Kode Transaksi', required=True, default=lambda self: 'SBR-' + datetime.now().strftime('%Y%m%d%H%M%S'))
    customer_id = fields.Many2one('gadai.customer', string='Customer', required=True)
    tanggal = fields.Date(string='Tanggal Transaksi', default=fields.Date.today)
    durasi_hari = fields.Integer(string='Durasi (Hari)', default=30)
    jatuh_tempo = fields.Date(string='Jatuh Tempo', compute='_compute_jatuh_tempo', store=True)
    barang_ids = fields.One2many('gadai.barang', 'transaksi_id', string='Barang')
    total_taksiran = fields.Float(string='Total Taksiran', compute='_compute_total_taksiran', store=True)
    jumlah_pinjaman = fields.Float(string='Jumlah Pinjaman')
    
    bunga_persen = fields.Float(string='Bunga (%) per bulan', default=2.0)
    total_bunga = fields.Float(string='Total Bunga', compute='_compute_total_bunga', store=True)
    total_pelunasan = fields.Float(string='Total Pelunasan', compute='_compute_total_jumlah_bayar', store=True)

    is_lunas = fields.Boolean(string='Lunas', default=False)
    tanggal_lunas = fields.Date(string='Tanggal Pelunasan')
    
    diperpanjang = fields.Boolean(string='Sudah Diperpanjang?', default=False)
    transaksi_asal_id = fields.Many2one('gadai.transaksi', string='Perpanjangan dari')

    state = fields.Selection([
        ('aktif', 'Aktif'),
        ('lunas', 'Lunas'),
        ('diperpanjang', 'Diperpanjang'),
        ('dilelang', 'Dilelang')
    ], string='Status', default='aktif', tracking=True)

    @api.depends('barang_ids.nilai_taksiran')
    def _compute_total_taksiran(self):
        for record in self:
            record.total_taksiran = sum(b.nilai_taksiran for b in record.barang_ids)

    @api.depends('tanggal', 'durasi_hari')
    def _compute_jatuh_tempo(self):
        for record in self:
            if record.tanggal:
                record.jatuh_tempo = record.tanggal + timedelta(days=record.durasi_hari)

    @api.depends('total_taksiran', 'bunga_persen')
    def _compute_total_bunga(self):
        for record in self:
            record.total_bunga = (record.total_taksiran * record.bunga_persen) / 100

    @api.depends('jumlah_pinjaman', 'total_bunga')
    def _compute_total_jumlah_bayar(self):
        for record in self:
            record.total_pelunasan = record.jumlah_pinjaman + record.total_bunga

    @api.depends('total_taksiran', 'total_bunga')
    def _compute_total_pelunasan(self):
        for record in self:
            record.total_pelunasan = record.total_taksiran + record.total_bunga

    def action_tandai_lunas(self):
        for record in self:
            record.write({
                'is_lunas': True,
                'tanggal_lunas': fields.Date.today(),
                'state': 'lunas'
            })

    def action_tandai_lelang(self):
        for record in self:
            record.write({'state': 'dilelang'})

    def action_perpanjang(self):
        for record in self:
            if record.diperpanjang:
                raise UserError("Transaksi ini sudah pernah diperpanjang.")
            new_transaksi = self.env['gadai.transaksi'].create({
                'customer_id': record.customer_id.id,
                'tanggal': fields.Date.today(),
                'durasi_hari': record.durasi_hari,
                'bunga_persen': record.bunga_persen,
                'transaksi_asal_id': record.id
            })
            for barang in record.barang_ids:
                barang.copy({'transaksi_id': new_transaksi.id})
            record.write({
                'diperpanjang': True,
                'state': 'diperpanjang'
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Transaksi Gadai Baru',
                'res_model': 'gadai.transaksi',
                'view_mode': 'form',
                'res_id': new_transaksi.id,
                'target': 'current'
            }
