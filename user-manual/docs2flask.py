from os import walk, path as os_path, listdir, makedirs
import re
from shutil import copyfile, copytree, rmtree
from bs4 import BeautifulSoup
from global_params import pr_app_path, pr_html_output


templates_folder = os_path.join(pr_app_path, 'templates')
static_folder = os_path.join(pr_app_path, 'static')

flask_docs_html_templates = os_path.join(templates_folder, 'docs')
flask_static_sphinx_folder = os_path.join(static_folder, 'sphinx')

rmtree(flask_docs_html_templates, ignore_errors=True)
rmtree(flask_static_sphinx_folder, ignore_errors=True)

makedirs(flask_docs_html_templates, exist_ok=True)
makedirs(flask_static_sphinx_folder, exist_ok=True)


def update_static_paths(directory, old_path, new_path):
    for root, dirs, files in walk(directory):

        for file in files:
            if file.endswith('.html'):
                file_path = os_path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Replace the static paths
                updated_content = re.sub(old_path, new_path, content)

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)




pr_UserManual_dir_files = [os_path.basename(f) for f in listdir(
    pr_html_output)]


for fileName in pr_UserManual_dir_files:

    __fullpath1 = os_path.join(
        pr_html_output, fileName)

    if fileName in ['.doctrees', '_sources']:
        __fullpath2 = os_path.join(
        flask_static_sphinx_folder, fileName)
        copytree(src=__fullpath1, dst=__fullpath2)

    elif fileName.endswith('.html'):

        __fullpath2 = os_path.join(
            flask_docs_html_templates, fileName)

        copyfile(__fullpath1, __fullpath2)

    elif fileName.endswith('.js'):
    
        __fullpath2 = os_path.join(
            flask_static_sphinx_folder, fileName)

        copyfile(__fullpath1, __fullpath2)


pr_static_path = os_path.join(pr_html_output, '_static')
docst_static_files = [f for f in listdir(pr_static_path)]

for dirf in docst_static_files:

    try:
        __fullpath1 = os_path.join(
            pr_static_path, dirf)

        __fullpath2 = os_path.join(
            flask_static_sphinx_folder, dirf)

        copyfile(__fullpath1, __fullpath2)

    except Exception as err:
        print(f'{dirf} not copied: {str(err)}')

update_static_paths(flask_docs_html_templates,
                    '_static/js', '/static/sphinx/')

update_static_paths(flask_docs_html_templates,
                    '_static/css', '/static/sphinx/')

update_static_paths(flask_docs_html_templates,
                    '_static/', '/static/sphinx/')


update_static_paths(flask_docs_html_templates,
                    '_images/', '/static/images/')

update_static_paths(flask_docs_html_templates,
                    '_sources/', '/static/sphinx/_sources/')

update_static_paths(flask_docs_html_templates,
                    '.doctrees/', '/static/sphinx/.doctrees/')


def create_comment_div(section_id):
    return BeautifulSoup(f'''
    <div class="comment-form" >
      <p> User comments:</p>
      <textarea id='id-user-comment-{section_id}' placeholder="Add a comment..." style="width: 80vw; height: 8vh"></textarea>
      <div>
        <button class='btn btn-success'
        onclick="update_comments(id='id-user-comment-{section_id}', filePath=window.location.href)">Send</button>
      </div>
    </div>
    ''', 'html.parser')


def add_script():

    strt = '''
        <script src="https://code.jquery.com/jquery-3.6.3.min.js"></script>
        <script>

            function update_comments(id) {
            let comnt = document.getElementById(id).value;

            $.post("/update_comments", 
                    {request_data: JSON.stringify({
                    comment: comnt, 
                    sec_id: id 
                    })}, 
                    function(response) {
                if (response.code === 400) {
                    alert(response.message);
                    return;
                }
            });
            }

        </script>
    '''

    return BeautifulSoup(strt, 'html.parser')


def add_comment_section(directory=pr_html_output):

    for root, dirs, files in walk(directory):
        for file in files:
            if file.endswith('.html'):

                file_path = os_path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')

                for section in soup.find_all('section'):
                    comment_div = create_comment_div(section.get('id', ''))
                    section.append(comment_div)

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(str(soup))


def update_html_files(directory):

    for root, dirs, files in walk(directory):
        for file in files:
            if file.endswith('.html'):

                file_path = os_path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')

                for script in soup.find_all('script', src=True):
                    a_ref = script['src']
                    if 'searchindex.js' in a_ref:
                        script['src'] = "/static/sphinx/searchindex.js"

                for form in soup.find_all('form', action=True):

                    a_ref = form['action']
                    if a_ref.endswith('.html'):
                        a_ref = a_ref.split('.')
                        form['action'] = "{{ " + \
                            f"url_for('lion.{a_ref[0].lower()}')" + " }} "

                for link in soup.find_all('link', href=True):

                    a_ref = link['href']

                    if a_ref.endswith('.html'):
                        a_ref = a_ref.split('.')
                        link['href'] = "{{ " + \
                            f"url_for('lion.{a_ref[0].lower()}')" + " }} "

                for a in soup.find_all('a', href=True):
                    a_ref = a['href']
                    if a_ref == 'index.html':
                        a['href'] = "{{ " + "url_for('lion.docs')" + " }} "
                    
                    elif a_ref.endswith('.html'):

                        a_ref = a_ref.split('.')
                        a['href'] = "{{ " + \
                            f"url_for('lion.{a_ref[0].lower()}')" + " }}"

                    elif '.html#' in a_ref.lower():
                        a_ref = a_ref.split('.')
                        a['href'] = "{{ " + f"url_for('lion.{a_ref[0].lower()}')" + " }}" + \
                            a_ref[1].replace('html', '/')

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(str(soup))


# add_comment_section()
update_html_files(flask_docs_html_templates)
