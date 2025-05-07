from odoo import models, fields

class GadaiBarang(models.Model):
    _name = 'gadai.barang'
    _description = 'Data Barang Gadai'

    name = fields.Char(string='Nama Barang', required=True)
    jenis = fields.Selection([
        ('emas', 'Emas'),
        ('elektronik', 'Elektronik'),
        ('lainnya', 'Lainnya'),
    ], string='Jenis Barang', required=True)
    nilai_taksiran = fields.Float(string='Nilai Taksiran')
    spesifikasi = fields.Char(string='Spesifikasi')
    transaksi_id = fields.Many2one('gadai.transaksi', string='Transaksi Gadai')
