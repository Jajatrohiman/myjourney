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
    jumlah_pinjaman = fields.Float(string='Jumlah Pinjaman', required=True)
    nilai_taksiran = fields.Float(string='Nilai Taksiran')
    bunga_persen = fields.Float(string='Bunga (%) per bulan', default=2.0)
    total_bunga = fields.Float(string='Total Bunga', compute='_compute_total_bunga', store=True)
    total_pelunasan = fields.Float(string='Total Pelunasan Yg Seharusnya', compute='_compute_total_pelunasan', store=True)
    currency_id = fields.Many2one('res.currency', string='Mata Uang', 
                                 default=lambda self: self.env.company.currency_id.id)

    is_lunas = fields.Boolean(string='Lunas', default=False)
    tanggal_lunas = fields.Date(string='Tanggal Pelunasan')
    nominal_pelunasan = fields.Float(string='Nominal Pelunasan Aktual', help='Nominal yang dibayarkan saat penebusan barang')
    selisih_pelunasan = fields.Float(string='Selisih Pelunasan', compute='_compute_selisih_pelunasan', store=True)
    catatan_pelunasan = fields.Text(string='Catatan Pelunasan')
    
    diperpanjang = fields.Boolean(string='Sudah Diperpanjang?', default=False)
    transaksi_asal_id = fields.Many2one('gadai.transaksi', string='Perpanjangan dari')

    state = fields.Selection([
        ('aktif', 'Aktif'),
        ('lunas', 'Lunas'),
        ('diperpanjang', 'Diperpanjang'),
        ('dilelang', 'Dilelang')
    ], string='Status', default='aktif', tracking=True)

    @api.depends('tanggal', 'durasi_hari')
    def _compute_jatuh_tempo(self):
        for record in self:
            if record.tanggal:
                record.jatuh_tempo = record.tanggal + timedelta(days=record.durasi_hari)
            else:
                record.jatuh_tempo = False
                
    @api.depends('jumlah_pinjaman', 'bunga_persen', 'durasi_hari')
    def _compute_total_bunga(self):
        for record in self:
            # Menghitung bunga berdasarkan durasi dalam bulan (dibulatkan ke atas)
            bulan = (record.durasi_hari or 0) / 30.0
            if bulan < 1:
                bulan = 1
            bunga = (record.jumlah_pinjaman * record.bunga_persen * bulan) / 100
            record.total_bunga = bunga
            
    @api.depends('jumlah_pinjaman', 'total_bunga')
    def _compute_total_pelunasan(self):
        for record in self:
            record.total_pelunasan = record.jumlah_pinjaman + record.total_bunga
            
    @api.depends('total_pelunasan', 'nominal_pelunasan')
    def _compute_selisih_pelunasan(self):
        for record in self:
            if record.nominal_pelunasan and record.total_pelunasan:
                record.selisih_pelunasan = record.nominal_pelunasan - record.total_pelunasan
            else:
                record.selisih_pelunasan = 0.0
            
    @api.onchange('barang_ids')
    def _onchange_barang_ids(self):
        """
        Method ini hanya untuk menampilkan nilai taksiran total dari barang
        sebagai informasi untuk user.
        """
        for record in self:
            record.nilai_taksiran = sum(barang.nilai_taksiran for barang in record.barang_ids)
    
    @api.onchange('jumlah_pinjaman', 'bunga_persen', 'durasi_hari')
    def _onchange_pinjaman_fields(self):
        """
        Method ini untuk memastikan total bunga dan total pelunasan 
        langsung terupdate saat ada perubahan di UI
        """
        bulan = (self.durasi_hari or 0) / 30.0
        if bulan < 1:
            bulan = 1
        self.total_bunga = (self.jumlah_pinjaman * self.bunga_persen * bulan) / 100
        self.total_pelunasan = self.jumlah_pinjaman + self.total_bunga

    def action_tandai_lelang(self):
        for record in self:
            record.write({'state': 'dilelang'})

    def action_perpanjang(self):
        if not self.barang_ids:
            raise UserError("Tidak ada barang yang dapat diperpanjang.")
        for record in self:
            if record.diperpanjang:
                raise UserError("Transaksi ini sudah pernah diperpanjang.")
            new_transaksi = self.env['gadai.transaksi'].create({
                'customer_id': record.customer_id.id,
                'tanggal': fields.Date.today(),
                'durasi_hari': record.durasi_hari,
                'bunga_persen': record.bunga_persen,
                'jumlah_pinjaman': record.jumlah_pinjaman,
                'nilai_taksiran': record.nilai_taksiran,
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