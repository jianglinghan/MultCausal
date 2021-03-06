import os
import scipy
import random
import subprocess
import numpy as np
import pandas as pd
from utils import *
from multiprocessing import Pool
def worker(ind, f1, f2, out_f, step=1000): # f save in 'scipy.sparese.npz' format
		m1 = scipy.sparse.load_npz(f1) 
		m2 = scipy.sparse.load_npz(f2)
		m2 = csr_matrix(m2[ind*step:(ind+1)*step, :])
		if m1.shape[1] != m2.shape[0]:
			raise('dimention incompatible!')
		m = m1.dot(m2)	
		scipy.sparse.save_npz(out_f, m)
def dd_dot(d1, d2, out, parallel=True):
	print('Starting dd_dot ...')
	print('d1: ', d1)
	print('d2: ', d2)
	d1_lst = sorted(os.listdir(d1)) # sg_d
	d2_lst = sorted(os.listdir(d2)) # si_d
	if (d1_lst == d2_lst):
		print('d1 and d2 have the same order.')
	else:
		print('len(d1):', len(d1))
		print('len(d2):', len(d2))
		raise("ERROR: d1 doesn't match with d2!")
	print('ig d:', out)
	out_lst = os.listdir(out)
	out_lst = [i.split('.')[0] for i in out_lst]
	if len(out_lst) != len(d1_lst):
		pool = Pool(10)
		for ind, (d1_f, d2_f) in enumerate(zip(d1_lst, d2_lst)):
			if d1_f not in out_lst:
				common_f = d1_f
				out_f = '{}/{}'.format(out, common_f)
				d1_f = '{}/{}'.format(d1, common_f)
				d2_f = '{}/{}'.format(d2, common_f)
	#			print('into loop')
				if parallel:
					pool.apply_async(worker,(ind, d1_f, d2_f, out_f,))
				else:
					worker(ind, d1_f, d2_f, out_f)
		pool.close()
		pool.join()
		go_on = True
	else:
		go_on = False
		print('dd mult done, results save to {}.'.format(out))
	return go_on 
def mult_casual(pre, sg_f, gg_f=None, reg=None, step=1):
	d, _ = os.path.split(pre)
	gdic_f = '{}_gdic.txt'.format(pre)
	pheno_f = '{}.pheno'.format(pre)
	_, sg_pre = os.path.split(sg_f) 
	sg_pre = sg_pre[:-7]
	sg_d = '{}/{}_sg'.format(d, sg_pre)
	is_d = '{}/{}_is'.format(d, sg_pre)
	ig_d = '{}/{}_ig'.format(d, sg_pre)
	if gg_f:
		_, gg_pre = os.path.split(gg_f)
		#gg_pre = gg_pre[:-8]
		print('gg_pre', gg_pre)
		geno_f = '{}/{}.{}.{}.isg.geno'.format(d, sg_pre, gg_pre, step)
		o = '{}.{}.{}.isg'.format(sg_pre, gg_pre, step)
	else:	
		geno_f = '{}/{}.is.geno'.format(d, sg_pre)
		o = '{}.is'.format(sg_pre)
	print('o', o)
	print('sg_d', sg_d)
	print('is_d', is_d)
	print('ig_d', ig_d)
	print('geno_f', geno_f)
	# main
	if not reg:
		go_on = dd_dot(is_d, sg_d, ig_d, parallel=False)
		if go_on:
			dd_dot(is_d, sg_d, ig_d)
			print('complting igmat ...')
		ig = os.listdir(ig_d)
		igmat = scipy.sparse.load_npz(os.path.join(ig_d, ig[0]))
		for i in ig[1:]:
			igmat += scipy.sparse.load_npz(os.path.join(ig_d, i))
		if gg_f:
			ggmat = scipy.sparse.load_npz(gg_f)
			ggmat = ggmat.power(step)
			igmat = igmat.dot(ggmat)
		igmat = igmat.toarray()
		igmat = rescale(igmat)
		gimat = igmat.transpose()
		gimat = pd.DataFrame(gimat)
		print('the final shape is :', gimat.shape)
		lmat = left(gdic_f)
		omat = pd.concat([lmat, gimat], ignore_index=True, axis=1)
		print('outputing geno to {}.'.format(geno_f))
		omat.to_csv(geno_f, header=None, index=False)
	order = 'gemma -g {} -p {} -lm 1 -outdir {} -o {}'.format(geno_f, pheno_f, d, o); print(order); os.system(order)
def mult_input(pre, sg_f):
	d, _ = os.path.split(pre)
	_, sg_pre = os.path.split(sg_f)
	sg_pre = sg_pre[:-7]
	si_f = '{}.geno'.format(pre)
	gdic_f = '{}_gdic.txt'.format(pre)
	sdic_f = '{}_sdic.txt'.format(pre)
	is_d = '{}/{}_is'.format(d, sg_pre) 
	si_d = '{}/{}_si'.format(d, sg_pre) 
	ig_d = '{}/{}_ig'.format(d, sg_pre)
	sg_d = '{}/{}_sg'.format(d, sg_pre)
	if not os.path.isdir(is_d):
		os.makedirs(is_d)
	if not os.path.isdir(si_d):
		os.makedirs(si_d)
	if not os.path.isdir(ig_d):
		os.makedirs(ig_d)
	if not os.path.isdir(sg_d):
		os.makedirs(sg_d)
	bimbam_2_is(si_f, is_d=is_d, si_d=si_d)	
	sg(sg_f, si_d=si_d, sg_d=sg_d, gdic_f=gdic_f, sdic_f=sdic_f)
def main_1():
#	mult_input('data/mult/arabi', 'data/arabi.20kb.sg.txt')
	for r in range(1, 10):
#		mult_casual('data/mult/arabi', 'data/arabi.20kb.sg.txt', gg_f='data/ppi_mult/atpin.2.no-weight.ppi.txt.npz', step=r)
		mult_casual('data/mult/arabi', 'data/arabi.20kb.sg.txt', gg_f='data/ppi_mult/atpin.ppi.2evidence.weight.txt.npz', step=r)
#		mult_casual('data/mult/arabi', 'data/arabi.20kb.sg.txt', step=r)
def main_2():
	print('Begin.')
	sg_d = 'data/mateqtl'
	ppi_d = 'data/ppi_mult'
	for i in os.listdir(sg_d):
		if i.endswith('sg.txt'):
		#	if i != 'arabi.0.01.1e+06Dist.p.sg.txt':
			for k in range(9, 5, -1):
				if i.startswith('arabi.5e-0{}'.format(k)):
					print('sg is :', i)
					i = '{}/{}'.format(sg_d, i)
					mult_input('data/mult/arabi', i)
					mult_casual('data/mult/arabi', i)
					for j in os.listdir(ppi_d):
						if j.endswith('npz'):
							j = '{}/{}'.format(ppi_d, j)
							mult_casual('data/mult/arabi', i, gg_f=j)
# test svm kernel
def main_3():
	d = 'data/svm'
	d2 = 'data/mateqtl'
	for i in os.listdir(d):
		if i.startswith('test.23445.153') and i.endswith('npz'):
			if i != 'test.23445.153.linear.kernel.npz':
				mult_casual('data/mult/arabi', 'data/arabi.20kb.sg.txt', gg_f='{}/{}'.format(d, i))

	for i in os.listdir(d):
		if i.startswith('test.23445.153') and i.endswith('npz'):
			for j in os.listdir(d2):
				if j.startswith('arabi.5e-06.1e+06') and j.endswith('sg.txt'):
					mult_casual('data/mult/arabi', '{}/{}'.format(d2, j), gg_f='{}/{}'.format(d, i))
				
def test():
	mult_input('./test/test')
	r = mult_casual('./test/test', 'test', reg=True)
	r = mult_casual('./test/test', 'test', gg_f='test/test.ppi.txt.npz')
	r = mult_input('data/mult/arabi', out_pre='data/mult/20kb', sg_pre='data/mult/arabi')
	r = mult_casual('data/mult/arabi', out_pre='data/mult/20kb', sg_pre='data/mult/arabi', gg_f='data/ppi_mult/atpin.2.no-weight.ppi.txt.npz')
	r = mult_casual('data/mult/arabi', out_pre='data/mult/20kb', sg_pre='data/mult/arabi', gg_f='data/ppi_mult/atpin.2.weight.ppi.txt.npz')
	r = mult_casual('data/mult/arabi', sg_f, reg=True)
	
if __name__ == '__main__':
	main_3()
#	mult_casual('data/mult/arabi', 'data/arabi.20kb.sg.txt', gg_f='data/svm/test.23445.153.linear.kernel.npz')
