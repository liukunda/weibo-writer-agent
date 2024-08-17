# -*- coding: utf-8 -*-
# Standard library imports.
import sqlite3,os,json,re,requests
# Related third party imports.
from flask import Flask, Blueprint,render_template,request,jsonify,url_for,current_app
from loguru import logger
from werkzeug.utils import secure_filename
from extends import (
    db,
)
# Local application/library specific imports.
from apps.weibo_UI.rag_run import *
from apps.weibo_UI.models import weibo_UI_Model

bp = Blueprint("weibo_UI", __name__, url_prefix='/weibo_UI',static_folder='static',template_folder='templates')


@bp.route('/index' )
def show():
    username='admin'
    return render_template('index.html',username=username)

@bp.route('/login',methods=['GET','POST'] )
def login():
    if request.method == 'GET':
        return render_template('pages_login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        users = weibo_UI_Model.query.all()
        #user = User.query.first()
        for user in users:
            print(user.name)
            if user.name==username and user.name==password:
                #db.session['is_login'] = True
                #db.session['username'] = username
                #db.session['pwd'] = password
                return render_template('index.html',username=username)
    

@bp.route('/add_user',methods=['GET','POST'] )
def add_user():
    if request.method == "POST":
        data = request.get_json()
        UserName=data['UserName']
        Pwd=data['Pwd']
        new_user = weibo_UI_Model()
        new_user.name = UserName
        new_user.text = Pwd
        db.session.add(new_user)
        db.session.commit()
        choose_dict={}
        choose_dict['result']=1
        return jsonify(choose_dict)
    return render_template('add_user.html')


@bp.route('/get_by_id',methods=['GET','POST'] )
def get_by_id():
    get_user = weibo_UI_Model.query.get(1)  # User.query.filter_by(id=get_id).first()
    return "编号：{0}，用戶名：{1}，邮箱：{2}".format(get_user.id, get_user.name, get_user.text)

@bp.route('/choose_model')
def choose_model():
    username="admin"
    return render_template('choose_model.html',username=username)
        
@bp.route('/choose_model_post',methods=["POST"])
def choose_model_post():
    if request.method == "POST":
        data = request.get_json()
        type_name=data['type_name']
        model_type=['-- pls choose --']
        if "choose_type" in type_name:
            try:
                res=os.popen("ps -ef | grep ollama").read()
                if 'ollama serve' in res:
                    model_type.append("ollama")
            except:
                logger.info('no ollama')
            try:
                res=os.popen("ps -ef | grep xinference").read()
                if 'xinference' in res:
                    model_type.append("xinference")
            except:
                logger.info('no xinference')
            choose_dict={}
            choose_dict['result']=1
            choose_dict['content']=model_type
            return jsonify(choose_dict)
        elif "choose_model" in type_name:
            type_select=data['type_select']
            model_list=[]
            if "ollama" in type_select:
                try:
                    res=os.popen("ollama list").read()
                    models=res.split('\n')
                    for index_i, item_i in enumerate(models):
                        if index_i == 0:
                            continue
                        model_list.append(item_i.split()[0])
                        print(item_i.split()[0])
                except:
                    logger.info('no ollama')
            choose_dict={}
            choose_dict['result']=1
            choose_dict['content']=model_list
            return jsonify(choose_dict)
        
@bp.route('/model_run',methods=["POST"])
def model_run():
    if request.method == "POST":
        data = request.get_json()
        type_name=data['type_name']
        model_select=data['model_name']
        KB_id=data['KB_id']
        top_selector=data['top_selector']
        top_K=int(top_selector)
        query=data['query']
        logger.info(query)
        url = 'http://127.0.0.1:4010/private/inference'
        # 检查响应状态代码
        res=''
        answer=vector_model_rag(url,KB_id,top_K,query,type_name,model_select)
        if answer['message'] == 'success':
            # 打印响应文本
            res=answer['data']['result']
        choose_dict={}
        choose_dict['result']=1
        choose_dict['content']=res
        #choose_dict['content']=response
        return jsonify(choose_dict)
    
@bp.route('/upload',methods=['GET','POST'])
def upload():
    username='admin'
    status=''
    if request.method == "POST":
        f = request.files['file']
        _filename_ascii_add_strip_re = re.compile(r'[^A-Za-z0-9_\u4E00-\u9FBF\u3040-\u30FF\u31F0-\u31FF.-]')
        filename = str(_filename_ascii_add_strip_re.sub('', '_'.join( # 新的正则
                f.filename.split()))).strip('._')
        filename=secure_filename(filename)
        save_path=os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.mkdir(current_app.config['UPLOAD_FOLDER'])
        f.save(save_path)
        status="upload ok"
    return render_template('upload_Document.html',username=username,status=status)

@bp.route('/Pic_upload',methods=['POST'])
def Pic_upload():
    if request.method == "POST":
        f = request.files['file']
        _filename_ascii_add_strip_re = re.compile(r'[^A-Za-z0-9_\u4E00-\u9FBF\u3040-\u30FF\u31F0-\u31FF.-]')
        filename = str(_filename_ascii_add_strip_re.sub('', '_'.join( # 新的正则
                f.filename.split()))).strip('._')
        filename=secure_filename(filename)
        save_path=os.path.join(current_app.config['UPLOAD_FOLDER_PIC'], filename)
        if not os.path.exists(current_app.config['UPLOAD_FOLDER_PIC']):
            os.mkdir(current_app.config['UPLOAD_FOLDER_PIC'])
        f.save(save_path)
        return 'upload success'

@bp.route('/self_media',methods=["POST","GET"])
def self_media():
    if request.method == "POST":
        data = request.get_json()
        if 'send_draft' in data['Type']:
            type_name=data['type_name']
            model_select=data['model_name']
            #split_document=data['split_document']
            KB_id=data['KB_select']
            title=data['title']
            thumb_media_id=data['thumb_media_id']
            query='以'+str(title)+'为题，写一篇文章'
            url = 'http://127.0.0.1:4010/private/inference'
            # 检查响应状态代码
            res=''
            answer=vector_model_rag(url,KB_id,top_K,query,type_name,model_select)
            choose_dict={}
            choose_dict['result']=0
            if answer['message'] == 'success':
                # 打印响应文本
                res=answer['data']['result']
                url_self_media= 'http://127.0.0.1:6050/wpp/draft_add'
                json_data_self_media = {
                    "title": title,
                    "content": res,
                    "thumb_media_id": thumb_media_id
                }
                # 发送请求并存储响应
                response_self_media = requests.post(url_self_media, json=json_data_self_media)
                self_media_res=response_self_media.json()
                if self_media_res['success']:
                    choose_dict['result']=1
            choose_dict['content']=res
            #choose_dict['content']=response
            return jsonify(choose_dict)
        elif 'selec_picture' in data['Type']:
            filepath=current_app.config['UPLOAD_FOLDER_PIC']
            files=os.listdir(filepath)
            file_dict={}
            file_dict['list']=files
            return jsonify(file_dict)
    username="admin"
    return render_template('self_media.html',username=username)
  
@bp.route('/submit_kb',methods=["POST","GET"])
def submit_kb():
    if request.method == "POST":
        data = request.get_json()
        #({'Dim':Dim,'Kb_id':Kb_id,'Kb_name':Kb_name,'desc':desc,'vector_store_name':vector_store_name,'embedding_model_name':embedding_model_name}),
        Dim=data['Dim']
        Dim=int(Dim)
        Kb_id=data['Kb_id']
        Kb_name=data['Kb_name']
        desc=data['desc']
        vector_store_name=data['vector_store_name']
        embedding_model_name=data['embedding_model_name']
        url = 'http://127.0.0.1:6020/vector/kb_add_one'
        json_data = {
          "kb_id": Kb_id,
          "kb_name": Kb_name,
          "kb_desc": desc,
          "vector_store_name": vector_store_name,
          "embedding_model_name": embedding_model_name,
          "dim": Dim
        }
        # 发送请求并存储响应
        response = requests.post(url, json=json_data)
        #print(response.json())
        # 检查响应状态代码
        res=''
        answer=response.json()
        choose_dict={}
        choose_dict['result']=0
        if answer['success']:
            choose_dict['result']=1
        #choose_dict['content']=res
        #choose_dict['content']=response
        return jsonify(choose_dict)
    username="admin"
    return render_template('upload_Document.html',username=username,status='')

@bp.route('/submit_doc',methods=["POST","GET"])
def submit_doc():
    if request.method == "POST":
        data = request.get_json()
        if 'selec_file' in data['Type']:
            filepath=current_app.config['UPLOAD_FOLDER']
            files=os.listdir(filepath)
            file_dict={}
            file_dict['list']=files
            return jsonify(file_dict)
        elif 'add_doc' in data['Type']:
            Kb_id_doc=data['Kb_id_doc']
            Doc_id=data['Doc_id']
            Doc_name=data['Doc_name']
            doc_file=data['doc_file']
            filepath=os.path.join(current_app.config['UPLOAD_FOLDER'], doc_file)
            doc_content_base64=data['doc_content_base64']
            url = 'http://127.0.0.1:6020/vector/doc_add_one'
            json_data = {
                "kb_id": Kb_id_doc,
                "doc_id": Doc_id,
                "doc_name": Doc_name,
                "doc_path": filepath,
                "doc_content_base64": doc_content_base64
            }
            # 发送请求并存储响应
            response = requests.post(url, json=json_data)
            #print(response.json())
            # 检查响应状态代码
            res=''
            answer=response.json()
            choose_dict={}
            choose_dict['result']=0
            if answer['success']:
                choose_dict['result']=1
            return jsonify(choose_dict)
    username='admin'
    return render_template('upload_Document.html',username=username,status='')

@bp.route('/submit_file_parsing',methods=["POST","GET"])
def submit_file_parsing():
    if request.method == "POST":
        data = request.get_json()
        if 'selec_file' in data['Type']:
            filepath=current_app.config['UPLOAD_FOLDER']
            files=os.listdir(filepath)
            file_dict={}
            file_dict['list']=files
            return jsonify(file_dict)
        elif 'add_file_parsing' in data['Type']:
            #'doc_id_parsing':doc_id_parsing,'doc_name_parsing':doc_name_parsing,'doc_file_parsing':doc_file_parsing,'doc_file_parsing_way':doc_file_parsing_way}
            doc_id_parsing=data['doc_id_parsing']
            doc_name_parsing=data['doc_name_parsing']
            doc_file_parsing=data['doc_file_parsing']
            doc_file_parsing_way=data['doc_file_parsing_way']
            filepath=os.path.join(current_app.config['UPLOAD_FOLDER'], doc_file_parsing)
            if 'doc_to_json' in doc_file_parsing_way:
                url = 'http://127.0.0.1:7030/document/docx_to_json'
            elif 'doc_to_text' in doc_file_parsing_way:
                url = 'http://127.0.0.1:6020/vector/doc_add_one'
            json_data = {
                    "doc_id": doc_id_parsing,
                    "doc_name": doc_name_parsing,
                    "doc_path": filepath
            }
            # 发送请求并存储响应
            response = requests.post(url, json=json_data)
            #print(response.json())
            # 检查响应状态代码
            res=''
            answer=response.json()
            choose_dict={}
            choose_dict['result']=0
            if answer['success']:
                choose_dict['result']=1
            return jsonify(choose_dict)
    username="admin"
    return render_template('upload_Document.html',username=username,status='')