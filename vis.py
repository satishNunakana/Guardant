import pandas as pd
import plotly
import plotly.graph_objs as go

import requests
import numpy as np
import psycopg2 as pg2
import json
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)


def connect(host):
    """Return a Guardant PostgreSQL psycopg2.connect() object.
    Returns:
        psycopg2.extensions.connection: psycopg2.connect() object.
    """

    ghdb_db = "ghdb"
    ghdb_user = "admin"
    ghdb_pw = "N7Tks0xPS"
    if host == "dev": host = "10.4.170.24"
    if host == "prd": host = "10.4.170.26"
    if host == "tst": host = "10.4.80.66"
    if host == "integration": host = "10.4.170.74"
    ghdb_host = host
    return pg2.connect(database=ghdb_db,
                       user=ghdb_user,
                       password=ghdb_pw,
                       host=ghdb_host)


def run_sql_query(query, host='10.4.170.26'):
    """Run an SQL query on the Guardant PostgreSQL server and return the
    result as a pandas dataframe.
    Args:
        query (str): SQL query string.
    Returns:
        pandas.core.frame.DataFrame: pandas dataframe containing SQL query.
    """

    return pd.read_sql_query(query, connect(host))


@app.route('/')
def index():
    return render_template("index.html")


def create_plot():
    N = 40
    x = np.linspace(0, 1, N)
    y = np.random.randn(N)
    df = pd.DataFrame({'x': x, 'y': y})  # creating a sample dataframe

    data = [
        go.Bar(
            x=df['x'],  # assign x as the dataframe column 'x'
            y=df['y']
        )
    ]

    graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


def create_percentage_list(tab):
    """Returns a list of MAF percentages. This will serve as the input for the histogram in
    plotly.
    :param tab: A table from snv_call or indel_call. It should contain a column called
    percentage."""
    return list(tab["percentage"])


@app.route('/maf_vis/snv:<gene>:<mut_aa>')
def snv_maf_vis(gene, mut_aa):
    sql_query = "SELECT * FROM snv_call WHERE gene = '{}' AND mut_aa = '{}' AND run_sample_id " \
                "LIKE 'A%' LIMIT 500".format(
        gene, mut_aa)
    table = run_sql_query(sql_query)
    bar = create_plot()
    histogram_data = create_percentage_list(table)
    return render_template('maf_vis.html', colnames=table.columns, df=table,
                           gene=gene, mut_aa=mut_aa,
                           histogram_data=histogram_data,
                           plot=bar)


@app.route('/maf_vis/indel:<gene>:<mut_aa>')
def indel_maf_vis(gene, mut_aa):
    sql_query = "SELECT * FROM indel_call WHERE gene = '{}' AND mut_aa = '{}' " \
                "AND run_sample_id LIKE 'A%'".format(
        gene, mut_aa)
    table = run_sql_query(sql_query)
    bar = create_plot()
    histogram_data = create_percentage_list(table)

    requests.packages.urllib3.disable_warnings()
    results = requests.get("http://wtf.ghdna.io/flowcell/input/FCID", verify=False).json()

    return render_template('maf_vis.html', colnames=table.columns, df=table,
                           gene=gene, mut_aa=mut_aa,
                           histogram_data=histogram_data,
                           plot=bar)


@app.route('/maf_vis/deletion:<gene>')
def deletion_vis(gene):
    sql_query = "SELECT * FROM deletion_call WHERE gene = '{}' AND run_sample_id LIKE 'A%' " \
                "AND is_deletion = True".format(
        gene)
    table = run_sql_query(sql_query)

    homdel_cn = table.loc[table["cnv_type"].eq("homdel"), "copy_number"].tolist()
    loh_cn = table.loc[table["cnv_type"].eq("loh"), "copy_number"].tolist()
    cov_del_cn = table.loc[table["cnv_type"].eq("cov_del"), "copy_number"].tolist()

    return render_template('deletion_vis.html', colnames=table.columns, df=table,
                           gene=gene,
                           homdel_cn=homdel_cn, loh_cn=loh_cn, cov_del_cn=cov_del_cn)

@app.route('/file/<path:path>')
@app.route('/igv/file/<path:path>')
def provide_file(path):
    # This is a workaround for Access-Control-Allow-Origin not present in the header of the request
    # from bifs
    return send_from_directory("/", path)


@app.route('/igv/aln:<run_sample_id>:<gene>')
def igv_aln(run_sample_id, gene):
    requests.packages.urllib3.disable_warnings()
    r = requests.get("https://wtf.ghdna.io/runid_from_run_sample_id/" + run_sample_id,
                           verify=False).json()
    run_id = r["results"][0]["runid"]
    r = requests.get("https://wtf.ghdna.io/flowcell/output/" + run_id).json()
    path = r["results"][0]["path"]
    cram_path = path + "/" + run_sample_id + ".short.bwamem.cram"
    resp = app.make_response(render_template("igv.html", gene=gene, cram_path = cram_path))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/igv/fusion:run_sample_id:gene')
def igv_fusion():
    pass


@app.route('/test_template')
def hello():
    return render_template('test_template.html', name="")
